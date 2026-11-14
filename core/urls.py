from django.contrib import admin
from django.urls import path
from rescate_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.registro_view, name='registro'),
    path('registrar-alimento/', views.registrar_alimento, name='registrar_alimento'),
    path('eliminar-registro/<int:pk>/', views.eliminar_registro, name='eliminar_registro'),
    path('motor-calculo/', views.motor_calculo_view, name='motor_calculo'),
    path('reportes-mrv/', views.reportes_mrv_view, name='reportes_mrv'),
    path('exportar-csv/', views.exportar_csv, name='exportar_csv'),
    path('simulador-donante/', views.simulador_donante_view, name='simulador_donante'),
    path('simulador-agregar/', views.simulador_agregar, name='simulador_agregar'),
    path('simulador-limpiar/', views.simulador_limpiar, name='simulador_limpiar'),
    path('simulador-eliminar/<int:pk>/', views.simulador_eliminar, name='simulador_eliminar'),
]