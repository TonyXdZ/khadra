from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.contrib.gis.gdal import OGRGeometry
from django.contrib.gis.geos import Point
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db import connection
from django.utils.translation import gettext as _
from phonenumber_field.modelfields import PhoneNumberField
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill


class Country(models.Model):
    name = models.CharField(_('Name'),max_length=75)
    iso2 = models.CharField(_('ISO2'), max_length=4)
    geom = models.MultiPolygonField(_('Geometry'), srid=4326)

    class Meta:
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')

    def __str__(self):
        return self.name

    @property
    def lat_lng(self):
        coords = self.geom.point_on_surface.coords
        return [coords[1], coords[0]]


class City(models.Model):

    name = models.CharField(_('Name'), max_length=75)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, verbose_name=_("Country"))
    geom = models.MultiPolygonField(_('Geometry'), srid=4326)

    class Meta:
        verbose_name = _('City')
        verbose_name_plural = _('Cities')

    def __str__(self):
        return self.name

    def get_random_location_point(self):
        """
        Generate a random Point geometry located within the current model's geometry field (`self.geom`).

        This function uses PostGIS's ST_GeneratePoints to create a single random point (npoints=1)
        inside the polygon or multipolygon geometry associated with the instance.

        Steps:
        1. Convert the geometry to EWKT (Extended Well-Known Text) format.
        2. Use raw SQL to call PostGIS: 
        ST_GeneratePoints(ST_GeomFromEWKT(...), 1), which returns a MULTIPOINT with 1 random point.
        3. Convert the result from the database into a Python OGRGeometry.
        4. Extract the coordinates from the MULTIPOINT and convert it to a GEOS Point object.
        5. Return this Point, preserving the spatial reference (SRID).

        This can be useful for placing random markers, e.g., assigning a random location inside a city or country boundary.
        """

        npoints = 1
        # Prepare sql command, return point as ewkt, passing the
        # bounding geometry as ewkt.
        ewkt = "'" + str(self.geom.ewkt) + "'"
        sql = f'SELECT ST_AsEWKT(ST_GeneratePoints(ST_GeomFromEWKT({ewkt}), {npoints}))'
        # Instanciate cursor.
        cursor = connection.cursor()
        # Inject coords into sql command and execute sql.
        cursor.execute(sql)
        row = cursor.fetchall()
        # Convert result to python geometry.
        multipoint = OGRGeometry(row[0][0])
        coords = multipoint.coords[0]
        srid = multipoint.srid
        random_point = Point(coords[0], coords[1], srid=srid)
        return random_point

    def save(self, * args, ** kwargs):
        """ Setting the country for each city automatically based on it's latitude and longtitude"""
        point_in_city = self.geom.point_on_surface
        country = Country.objects.filter(geom__contains=point_in_city)
        if country.exists():
            self.country = country.first()
        else:
            raise ValueError(_('This city is not contained by any country'))
        super().save(* args, ** kwargs)

    @property
    def lat_lng(self):
        coords = self.geom.point_on_surface.coords
        return [coords[1], coords[0]]


class Profile(models.Model):
    """
    Holds addintional information about every user
    """

    ACCOUNT_TYPE_CHOICES = (
        ('volunteer', _('Volunteer')),
        ('manager', _('Manager')),
        )
    
    user = models.OneToOneField(User, verbose_name=_('User'), on_delete=models.CASCADE)

    country = models.ForeignKey(Country, verbose_name=_('Country'), on_delete=models.SET_NULL, null=True)

    city = models.ForeignKey(City, verbose_name=_('City'), on_delete=models.SET_NULL, null=True)
    
    geo_location = models.PointField(verbose_name=_('Geolocation'), srid=4326, null=True, blank=True)

    account_type = models.CharField(_('Account type'), max_length=100, choices=ACCOUNT_TYPE_CHOICES, default='volunteer')
    
    #Original size profile pic
    profile_pic = models.ImageField(_("Profile picture"), default=None, upload_to='profile_pics', blank=True, null=True)

    #Thumbnail of profile pic to be displayed in the profile page
    profile_pic_256 = ImageSpecField(source='profile_pic',
        processors=[ResizeToFill(256, 256)],
        format='JPEG',
        options={'quality': 100})

    #Thumbnail of profile pic to be displayed in feed and maps page along side the username
    profile_pic_64 = ImageSpecField(source='profile_pic',
        processors=[ResizeToFill(64, 64)],
        format='JPEG',
        options={'quality': 100})

    phone_number = PhoneNumberField(_('Phone number'), help_text=_('Personal phone number'))
    bio = models.TextField(
        _('Biography'),
        max_length=500, 
        blank=True, 
        null=True,
        help_text=_('Tell us about yourself (500 characters max)')
    )

    def __str__(self):
        return f'{self.user.username} profile'

    def get_profile_pic_64(self):
        """
        Return profile_pic_64 if it exists
        else return placeholder (images/profile_placeholder_64x64.svg)
        TODO : check if user is logged in using a social account
        and get the avatar from it
        """
        if self.profile_pic_64:
            return self.profile_pic_64.url
        else:
            return staticfiles_storage.url('images/profile_placeholder_64x64.svg')
    
    def get_profile_pic_256(self):
        """
        Return profile_pic_256 if it exists
        else return placeholder (images/profile_placeholder_64x64.svg)
        TODO : check if user is logged in using a social account
        and get the avatar from it
        """
        if self.profile_pic_256:
            return self.profile_pic_256.url
        else:
            return staticfiles_storage.url('images/profile_placeholder.svg')

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')