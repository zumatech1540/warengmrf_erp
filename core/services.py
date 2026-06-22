from core.models import Department

def get_or_create_department(name):
    dept, _ = Department.objects.get_or_create(name=name)
    return dept