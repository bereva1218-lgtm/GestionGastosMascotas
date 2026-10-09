from django.http import HttpResponse
from django.shortcuts import render


# Create your views here.
def primeravista(request):
    return render(request, 'index.html')

def cargamosMensaje(request):
    return HttpResponse("Hola, este es un mensaje de prueba para verificar que la vista funciona correctamente.")

def objeto_view(request):
    # crear un objeto de ejemplos
    objeto = {
        'nombre': 'Coleccionable de musica',
        'descripcion': 'guitarra de coleccion',
        'precio': 10.99,
        'disponible': True
    }
    #pasar el objeto al contexto de la plantilla
    return render (request, "objeto.html", {'objeto': objeto})