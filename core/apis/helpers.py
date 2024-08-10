# Create your functions here

def listdistinctfieldvalues(model, field):
    datas = model.objects.values_list(field, flat=True).distinct()
    return datas
