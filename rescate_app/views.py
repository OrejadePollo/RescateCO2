import csv
import json
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import FactorEmision, RegistroAlimento, SimulacionDonacion

def inicializar_datos():
    if FactorEmision.objects.count() == 0:
        datos_iniciales = [
            ('Frutas y verduras', 0.85, 'EPA WARM / Verra VM0046', '2026'),
            ('Lácteos', 3.20, 'IPCC / DEFRA', '2026'),
            ('Panadería', 1.40, 'EPA WARM', '2026'),
            ('Carnes y embutidos', 14.50, 'IPCC / FAO', '2026'),
            ('Abarrotes', 1.80, 'INECC / SEMARNAT', '2026'),
            ('Alimentos preparados', 2.50, 'Verra VM0046', '2026'),
            ('Otros', 1.10, 'Estándar General MRV', '2026'),
        ]
        for cat, factor, fuente, vig in datos_iniciales:
            FactorEmision.objects.create(
                categoria=cat,
                factor_kg_co2_por_kg=factor,
                fuente=fuente,
                vigencia=vig
            )

    if RegistroAlimento.objects.count() == 0:
        f_fruta = FactorEmision.objects.get(categoria='Frutas y verduras')
        f_pan = FactorEmision.objects.get(categoria='Panadería')
        f_lacteo = FactorEmision.objects.get(categoria='Lácteos')
        RegistroAlimento.objects.create(categoria=f_fruta, peso_kg=320.0, donante='Central de Abastos Veracruz', observaciones='Excedente estético apto para consumo')
        RegistroAlimento.objects.create(categoria=f_pan, peso_kg=85.5, donante='Panadería La Parroquia', observaciones='Recolección diaria matutina')
        RegistroAlimento.objects.create(categoria=f_lacteo, peso_kg=110.0, donante='Supermercado del Puerto', observaciones='Cadena de frío verificada a 4°C')

    if SimulacionDonacion.objects.count() == 0:
        f_fruta = FactorEmision.objects.get(categoria='Frutas y verduras')
        f_pan = FactorEmision.objects.get(categoria='Panadería')
        SimulacionDonacion.objects.create(empresa='Supermercados del Golfo S.A.', categoria=f_fruta, peso_kg=120.0, frecuencia='Semanal')
        SimulacionDonacion.objects.create(empresa='Supermercados del Golfo S.A.', categoria=f_pan, peso_kg=25.0, frecuencia='Diaria')

    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@rescateco2.org', 'rescate2026')
    if not User.objects.filter(username='capturista').exists():
        User.objects.create_user('capturista', 'captura@rescateco2.org', 'rescate2026')
    if not User.objects.filter(username='donante').exists():
        User.objects.create_user('donante', 'donante@empresa.com', 'donante2026')

def login_view(request):
    inicializar_datos()
    error = None
    if request.method == 'POST':
        usuario = request.POST.get('username', '').strip()
        clave = request.POST.get('password', '').strip()
        rol = request.POST.get('rol', 'Capturista')
        user = authenticate(request, username=usuario, password=clave)
        if user is not None:
            login(request, user)
            request.session['rol_usuario'] = rol
            if rol == 'Empresa Donante':
                return redirect('simulador_donante')
            return redirect('registro')
        else:
            error = 'Usuario o contraseña incorrectos. Usa los botones de acceso rápido inferiores.'
    return render(request, 'login.html', {'error': error})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='/login/')
def registro_view(request):
    inicializar_datos()
    registros = RegistroAlimento.objects.select_related('categoria').order_by('-fecha', '-id')
    categorias = FactorEmision.objects.all()
    total_kg = sum(float(r.peso_kg) for r in registros)
    total_co2 = sum(r.co2_evitado for r in registros)
    return render(request, 'registro.html', {
        'registros': registros,
        'categorias': categorias,
        'total_kg': total_kg,
        'total_co2': total_co2,
        'hoy': date.today().isoformat()
    })

@login_required(login_url='/login/')
def registrar_alimento(request):
    if request.method == 'POST':
        categoria_id = request.POST.get('categoria')
        peso_kg = request.POST.get('peso_kg')
        donante = request.POST.get('donante')
        fecha = request.POST.get('fecha') or date.today().isoformat()
        observaciones = request.POST.get('observaciones', '')
        
        cat = get_object_or_404(FactorEmision, id=categoria_id)
        registro = RegistroAlimento.objects.create(
            fecha=fecha,
            categoria=cat,
            peso_kg=peso_kg,
            donante=donante,
            observaciones=observaciones
        )
        return render(request, 'partials/fila_registro.html', {'registro': registro})
    return HttpResponse(status=400)

@login_required(login_url='/login/')
def eliminar_registro(request, pk):
    if request.method == 'DELETE':
        registro = get_object_or_404(RegistroAlimento, pk=pk)
        registro.delete()
        return HttpResponse('')
    return HttpResponse(status=400)

@login_required(login_url='/login/')
def motor_calculo_view(request):
    inicializar_datos()
    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')
    
    registros = RegistroAlimento.objects.select_related('categoria').all()
    if desde:
        registros = registros.filter(fecha__gte=desde)
    if hasta:
        registros = registros.filter(fecha__lte=hasta)

    total_kg = sum(float(r.peso_kg) for r in registros)
    total_co2 = sum(r.co2_evitado for r in registros)
    total_count = registros.count()

    categorias = FactorEmision.objects.all()
    etiquetas = []
    valores_co2 = []
    valores_peso = []

    for c in categorias:
        regs_cat = [r for r in registros if r.categoria_id == c.id]
        etiquetas.append(c.categoria)
        valores_co2.append(round(sum(r.co2_evitado for r in regs_cat), 2))
        valores_peso.append(round(sum(float(r.peso_kg) for r in regs_cat), 2))

    context = {
        'categorias': categorias,
        'total_kg': total_kg,
        'total_co2': total_co2,
        'total_count': total_count,
        'desde': desde,
        'hasta': hasta,
        'datos_grafica': json.dumps({
            'etiquetas': etiquetas,
            'valores_co2': valores_co2,
            'valores_peso': valores_peso
        })
    }
    return render(request, 'motor_calculo.html', context)

@login_required(login_url='/login/')
def reportes_mrv_view(request):
    inicializar_datos()
    donante_filtro = request.GET.get('donante', '').strip()
    registros = RegistroAlimento.objects.select_related('categoria').order_by('-fecha', '-id')
    if donante_filtro:
        registros = registros.filter(donante__icontains=donante_filtro)

    categorias = FactorEmision.objects.all()
    resumen_categorias = []
    for c in categorias:
        regs = [r for r in registros if r.categoria_id == c.id]
        peso = sum(float(r.peso_kg) for r in regs)
        co2 = sum(r.co2_evitado for r in regs)
        if peso > 0:
            resumen_categorias.append({
                'categoria': c.categoria,
                'factor': c.factor_kg_co2_por_kg,
                'fuente': c.fuente,
                'peso': peso,
                'co2': co2
            })

    total_kg = sum(float(r.peso_kg) for r in registros)
    total_co2 = sum(r.co2_evitado for r in registros)
    toneladas_co2 = total_co2 / 1000.0

    return render(request, 'reportes_mrv.html', {
        'registros': registros,
        'resumen_categorias': resumen_categorias,
        'total_kg': total_kg,
        'total_co2': total_co2,
        'toneladas_co2': toneladas_co2,
        'donante_filtro': donante_filtro,
        'fecha_actual': date.today()
    })

def _contexto_simulador():
    simulaciones = SimulacionDonacion.objects.select_related('categoria').order_by('-id')
    total_peso_lote = sum(float(s.peso_kg) for s in simulaciones)
    total_co2_lote = sum(s.co2_evitado_lote for s in simulaciones)
    total_peso_mes = sum(s.peso_proyectado_kg for s in simulaciones)
    total_co2_mes = sum(s.co2_evitado_proyectado for s in simulaciones)
    toneladas_co2_mes = total_co2_mes / 1000.0

    personas_alimentadas = int(total_peso_mes * 2.5)
    arboles_equiv = round(total_co2_mes / 21.0, 1)
    km_auto_evitados = round(total_co2_mes / 0.19, 0)
    valor_bono_mxn = round(toneladas_co2_mes * 14.07 * 18.11, 2)

    empresa_principal = simulaciones[0].empresa if simulaciones.exists() else "Empresa Donante S.A. de C.V."

    etiquetas = []
    valores_co2 = []
    for c in FactorEmision.objects.all():
        co2_cat = sum(s.co2_evitado_proyectado for s in simulaciones if s.categoria_id == c.id)
        if co2_cat > 0:
            etiquetas.append(c.categoria)
            valores_co2.append(round(co2_cat, 2))

    return {
        'simulaciones': simulaciones,
        'categorias': FactorEmision.objects.all(),
        'total_peso_lote': total_peso_lote,
        'total_co2_lote': total_co2_lote,
        'total_peso_mes': total_peso_mes,
        'total_co2_mes': total_co2_mes,
        'toneladas_co2_mes': toneladas_co2_mes,
        'personas_alimentadas': personas_alimentadas,
        'arboles_equiv': arboles_equiv,
        'km_auto_evitados': km_auto_evitados,
        'valor_bono_mxn': valor_bono_mxn,
        'empresa_principal': empresa_principal,
        'fecha_actual': date.today(),
        'datos_grafica_sim': json.dumps({'etiquetas': etiquetas, 'valores': valores_co2})
    }

@login_required(login_url='/login/')
def simulador_donante_view(request):
    inicializar_datos()
    return render(request, 'simulador_donante.html', _contexto_simulador())

@login_required(login_url='/login/')
def simulador_agregar(request):
    if request.method == 'POST':
        empresa = request.POST.get('empresa', 'Mi Empresa Donante').strip()
        categoria_id = request.POST.get('categoria')
        peso_kg = request.POST.get('peso_kg', 0)
        frecuencia = request.POST.get('frecuencia', 'Unica')
        cat = get_object_or_404(FactorEmision, id=categoria_id)
        SimulacionDonacion.objects.create(
            empresa=empresa,
            categoria=cat,
            peso_kg=peso_kg,
            frecuencia=frecuencia
        )
        return render(request, 'partials/panel_simulador.html', _contexto_simulador())
    return HttpResponse(status=400)

@login_required(login_url='/login/')
def simulador_eliminar(request, pk):
    if request.method == 'DELETE':
        sim = get_object_or_404(SimulacionDonacion, pk=pk)
        sim.delete()
        return render(request, 'partials/panel_simulador.html', _contexto_simulador())
    return HttpResponse(status=400)

@login_required(login_url='/login/')
def simulador_limpiar(request):
    if request.method == 'POST':
        SimulacionDonacion.objects.all().delete()
        return render(request, 'partials/panel_simulador.html', _contexto_simulador())
    return HttpResponse(status=400)

@login_required(login_url='/login/')
def exportar_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="Reporte_MRV_Rescate_CO2.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(['Lote ID', 'Fecha', 'Categoria', 'Peso (kg)', 'Factor (kg CO2e/kg)', 'CO2e Evitado (kg)', 'Donante', 'Fuente Metodologica', 'Observaciones'])
    for r in RegistroAlimento.objects.select_related('categoria').all():
        writer.writerow([
            f"LOTE-{r.id:04d}",
            r.fecha,
            r.categoria.categoria,
            r.peso_kg,
            r.categoria.factor_kg_co2_por_kg,
            round(r.co2_evitado, 2),
            r.donante,
            r.categoria.fuente,
            r.observaciones
        ])
    return response