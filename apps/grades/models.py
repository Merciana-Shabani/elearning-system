from django.db import models
from django.conf import settings


class GradeCategory(models.Model):
    """
    Grade category in the gradebook.
    Mirrors Moodle's mdl_grade_categories.
    """
    AGGREGATION_MEAN = 1
    AGGREGATION_WEIGHTED_MEAN = 2
    AGGREGATION_SIMPLE_WEIGHTED = 3
    AGGREGATION_LOWEST = 4
    AGGREGATION_HIGHEST = 5
    AGGREGATION_SUM = 6
    AGGREGATION_NATURAL = 13

    AGGREGATION_CHOICES = [
        (AGGREGATION_MEAN, 'Mean of grades'),
        (AGGREGATION_WEIGHTED_MEAN, 'Weighted mean of grades'),
        (AGGREGATION_SIMPLE_WEIGHTED, 'Simple weighted mean'),
        (AGGREGATION_LOWEST, 'Lowest grade'),
        (AGGREGATION_HIGHEST, 'Highest grade'),
        (AGGREGATION_SUM, 'Sum of grades'),
        (AGGREGATION_NATURAL, 'Natural weighting'),
    ]

    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE, related_name='grade_categories'
    )
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children'
    )
    name = models.CharField(max_length=255)
    aggregation = models.IntegerField(choices=AGGREGATION_CHOICES, default=AGGREGATION_NATURAL)
    keeps_high = models.IntegerField(default=0)
    drop_low = models.IntegerField(default=0)
    aggregation_coeff = models.DecimalField(max_digits=10, decimal_places=5, default=0)
    aggregation_coeff_extra = models.DecimalField(max_digits=10, decimal_places=5, default=0)
    depth = models.IntegerField(default=2)
    path = models.CharField(max_length=255, blank=True)
    hidden = models.BooleanField(default=False)

    class Meta:
        db_table = 'elening_grade_categories'
        verbose_name = 'Grade Category'
        verbose_name_plural = 'Grade Categories'

    def __str__(self):
        return f'{self.name} ({self.course.shortname})'


class GradeItem(models.Model):
    """
    An item in the gradebook (assignment, quiz, etc.).
    Mirrors Moodle's mdl_grade_items.
    """
    ITEM_COURSE = 'course'
    ITEM_CATEGORY = 'category'
    ITEM_MANUAL = 'manual'
    ITEM_MOD = 'mod'

    ITEM_TYPE_CHOICES = [
        (ITEM_COURSE, 'Course total'),
        (ITEM_CATEGORY, 'Category total'),
        (ITEM_MANUAL, 'Manual grade'),
        (ITEM_MOD, 'Activity module'),
    ]

    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE, related_name='grade_items'
    )
    category = models.ForeignKey(
        GradeCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='grade_items'
    )
    item_name = models.CharField(max_length=255)
    item_type = models.CharField(max_length=30, choices=ITEM_TYPE_CHOICES, default=ITEM_MOD)
    item_module = models.CharField(max_length=30, blank=True)
    item_instance = models.IntegerField(null=True, blank=True)
    grade_max = models.DecimalField(max_digits=10, decimal_places=5, default=100)
    grade_min = models.DecimalField(max_digits=10, decimal_places=5, default=0)
    grade_pass = models.DecimalField(max_digits=10, decimal_places=5, default=0)
    weight_override = models.BooleanField(default=False)
    aggregation_coeff = models.DecimalField(max_digits=10, decimal_places=5, default=0)
    aggregation_coeff_extra = models.DecimalField(max_digits=10, decimal_places=5, default=0)
    display = models.IntegerField(default=0)
    decimals = models.IntegerField(null=True, blank=True)
    hidden = models.IntegerField(default=0)
    locked = models.DecimalField(max_digits=10, decimal_places=5, default=0)
    locktime = models.IntegerField(default=0)
    needsupdate = models.IntegerField(default=0)
    sortorder = models.IntegerField(default=1)
    outcomeid = models.IntegerField(null=True, blank=True)
    scaleid = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'elening_grade_items'
        ordering = ['sortorder']

    def __str__(self):
        return f'{self.item_name} ({self.course.shortname})'


class Grade(models.Model):
    """
    A grade for a user on a grade item.
    Mirrors Moodle's mdl_grade_grades.
    """
    item = models.ForeignKey(GradeItem, on_delete=models.CASCADE, related_name='grades')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='grades'
    )
    raw_grade = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    raw_grade_max = models.DecimalField(max_digits=10, decimal_places=5, default=100)
    raw_grade_min = models.DecimalField(max_digits=10, decimal_places=5, default=0)
    raw_scale_id = models.IntegerField(null=True, blank=True)
    finalgrade = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    hidden = models.IntegerField(default=0)
    locked = models.DecimalField(max_digits=10, decimal_places=5, default=0)
    locktime = models.IntegerField(default=0)
    exported = models.IntegerField(default=0)
    overridden = models.IntegerField(default=0)
    excluded = models.IntegerField(default=0)
    feedback = models.TextField(blank=True)
    feedbackformat = models.IntegerField(default=1)
    information = models.TextField(blank=True)
    informationformat = models.IntegerField(default=0)
    timecreated = models.IntegerField(null=True, blank=True)
    timemodified = models.IntegerField(null=True, blank=True)
    aggregationstatus = models.CharField(max_length=10, default='unknown')
    aggregationweight = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elening_grades'
        unique_together = ('item', 'user')

    def __str__(self):
        return f'{self.user} on {self.item}: {self.finalgrade}'

    @property
    def percentage(self):
        if self.finalgrade is None:
            return None
        range_val = float(self.item.grade_max) - float(self.item.grade_min)
        if range_val == 0:
            return 0
        return round(
            (float(self.finalgrade) - float(self.item.grade_min)) / range_val * 100, 1
        )
