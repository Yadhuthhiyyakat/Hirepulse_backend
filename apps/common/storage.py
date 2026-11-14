import os
import json
import logging
import mimetypes
import urllib.request
import urllib.error
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage, FileSystemStorage
from django.utils.deconstruct import deconstructible
from storages.backends.s3boto3 import S3Boto3Storage

logger = logging.getLogger(__name__)


@deconstructible
class SupabaseStorage(Storage):
    """
    Native Supabase Storage backend for Django with transparent local fallback.
    Connects directly to the Supabase Storage REST API using SUPABASE_URL and SUPABASE_KEY.
    If Supabase Storage is unconfigured, unreachable, or encounters an RLS/bucket error,
    it automatically falls back to local media storage without failing user uploads.
    """

    def __init__(self, bucket_name=None, supabase_url=None, supabase_key=None, is_public=True):
        self.supabase_url = (
            supabase_url
            or getattr(settings, 'SUPABASE_URL', '')
            or os.environ.get('SUPABASE_URL', '')
        ).rstrip('/')
        self.supabase_key = (
            supabase_key
            or getattr(settings, 'SUPABASE_KEY', '')
            or os.environ.get('SUPABASE_KEY', '')
            or os.environ.get('SUPABASE_ANON_KEY', '')
            or os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
        )
        self.bucket_name = (
            bucket_name
            or getattr(settings, 'SUPABASE_BUCKET_NAME', '')
            or os.environ.get('SUPABASE_BUCKET_NAME', 'hirepulse')
        )
        self.is_public = is_public
        self._local_storage = None

    @property
    def local_storage(self):
        if self._local_storage is None:
            self._local_storage = FileSystemStorage(
                location=settings.MEDIA_ROOT,
                base_url=settings.MEDIA_URL
            )
        return self._local_storage

    @property
    def headers(self):
        return {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
        }

    def _get_api_url(self, path):
        clean_path = path.lstrip('/')
        return f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{clean_path}"

    def _create_bucket_if_missing(self):
        """Attempts to auto-create public bucket in Supabase if it does not exist."""
        try:
            bucket_url = f"{self.supabase_url}/storage/v1/bucket"
            payload = json.dumps({'id': self.bucket_name, 'name': self.bucket_name, 'public': True}).encode('utf-8')
            req = urllib.request.Request(
                bucket_url,
                data=payload,
                headers={**self.headers, 'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                pass
        except Exception:
            pass

    def _save(self, name, content):
        clean_name = name.lstrip('/')

        if not self.supabase_url or not self.supabase_key:
            return self.local_storage._save(clean_name, content)

        url = self._get_api_url(clean_name)
        content_type, _ = mimetypes.guess_type(clean_name)
        content_type = content_type or 'application/octet-stream'

        if hasattr(content, 'seek'):
            content.seek(0)
        data = content.read() if hasattr(content, 'read') else content

        req_headers = {
            **self.headers,
            'Content-Type': content_type,
            'x-upsert': 'true',
        }

        # 1. Attempt POST to Supabase Storage (fast 3s timeout)
        req = urllib.request.Request(url, data=data, headers=req_headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                return clean_name
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                self._create_bucket_if_missing()

            # Retry with PUT (upsert)
            req_put = urllib.request.Request(url, data=data, headers=req_headers, method='PUT')
            try:
                with urllib.request.urlopen(req_put, timeout=3) as resp:
                    return clean_name
            except Exception as retry_err:
                logger.warning(
                    "Supabase Storage upload failed (%s). Falling back to local storage for '%s'.",
                    retry_err, clean_name
                )
        except Exception as e:
            logger.warning(
                "Supabase Storage upload failed (%s). Falling back to local storage for '%s'.",
                e, clean_name
            )

        # 2. Resilient local filesystem fallback
        file_to_save = ContentFile(data, name=clean_name) if isinstance(data, (bytes, bytearray)) else content
        if hasattr(content, 'seek'):
            try:
                content.seek(0)
            except Exception:
                pass
        return self.local_storage._save(clean_name, file_to_save)

    def _open(self, name, mode='rb'):
        clean_name = name.lstrip('/')
        if self.local_storage.exists(clean_name):
            return self.local_storage._open(clean_name, mode=mode)

        if not self.supabase_url or not self.supabase_key:
            return self.local_storage._open(clean_name, mode=mode)

        url = self._get_api_url(clean_name)
        req = urllib.request.Request(url, headers=self.headers, method='GET')
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                return ContentFile(resp.read(), name=name)
        except Exception as e:
            if self.local_storage.exists(clean_name):
                return self.local_storage._open(clean_name, mode=mode)
            raise IOError(f"Failed to read file '{name}': {e}")

    def delete(self, name):
        clean_name = name.lstrip('/')
        if self.local_storage.exists(clean_name):
            self.local_storage.delete(clean_name)

        if not self.supabase_url or not self.supabase_key:
            return
        url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}"
        payload = json.dumps({'prefixes': [clean_name]}).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=payload,
            headers={**self.headers, 'Content-Type': 'application/json'},
            method='DELETE',
        )
        try:
            with urllib.request.urlopen(req, timeout=2) as resp:
                pass
        except Exception:
            pass

    def exists(self, name):
        clean_name = name.lstrip('/')
        if self.local_storage.exists(clean_name):
            return True
        if not self.supabase_url or not self.supabase_key:
            return False
        url = self._get_api_url(clean_name)
        req = urllib.request.Request(url, headers=self.headers, method='HEAD')
        try:
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def url(self, name):
        if not name:
            return ''
        clean_name = name.lstrip('/')

        if self.local_storage.exists(clean_name):
            return self.local_storage.url(clean_name)

        if not self.supabase_url:
            return f"/media/{clean_name}"

        # For public files (logos, profile pictures)
        if self.is_public:
            return f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{clean_name}"

        # For private files (resumes), create signed URL valid for 1 hour
        sign_url = f"{self.supabase_url}/storage/v1/object/sign/{self.bucket_name}/{clean_name}"
        payload = json.dumps({'expiresIn': 3600}).encode('utf-8')
        req = urllib.request.Request(
            sign_url,
            data=payload,
            headers={**self.headers, 'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                signed = data.get('signedURL', '')
                if signed.startswith('http'):
                    return signed
                return f"{self.supabase_url}{signed}"
        except Exception:
            return f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{clean_name}"


# S3 compatible fallbacks (in case AWS S3 is explicitly chosen)
class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False


class PublicMediaStorage(S3Boto3Storage):
    location = 'media/public'
    default_acl = getattr(settings, 'AWS_DEFAULT_ACL', None)
    file_overwrite = False


class PrivateResumeStorage(S3Boto3Storage):
    location = 'media/resumes'
    default_acl = 'private'
    custom_domain = False
    querystring_auth = True
    querystring_expire = getattr(settings, 'AWS_QUERYSTRING_EXPIRE', 3600)
    file_overwrite = False
