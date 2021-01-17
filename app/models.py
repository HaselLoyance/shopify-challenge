from django.db import models
from app.helpers import file_field_to_b64str

class Image(models.Model):
    file = models.FileField(editable=False, upload_to='images/')
    is_local = models.BooleanField(default=True)
    hue1 = models.PositiveSmallIntegerField(default=10000)
    hue2 = models.PositiveSmallIntegerField(default=10000)
    hue3 = models.PositiveSmallIntegerField(default=10000)
    hue4 = models.PositiveSmallIntegerField(default=10000)
    effective_from = models.DateTimeField(auto_now_add=True)
    effective_to = models.DateTimeField(default=None, null=True)

    def to_dict(self) -> 'Image':
        return {
            'id': self.id,
            'data': file_field_to_b64str(self.file),
        }

    class Meta:
        db_table = 'images'
        indexes = [
            models.Index(fields=['hue1', 'hue2', 'hue3', 'hue4']),
            models.Index(fields=['hue1', 'hue2', 'hue3', 'hue4', 'effective_to']),
        ]
