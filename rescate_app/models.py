from django.db import models
from datetime import date

class FactorEmision(models.Model):
    categoria = models.CharField(max_length=100, unique=True)
    factor_kg_co2_por_kg = models.DecimalField(max_digits=6, decimal_places=2)
    fuente = models.CharField(max_length=150, default='IPCC / EPA WARM / Verra VM0046')
    vigencia = models.CharField(max_length=50, default='2026')

    def __str__(self):
        return f"{self.categoria} ({self.factor_kg_co2_por_kg} kg CO2e/kg)"

class RegistroAlimento(models.Model):
    fecha = models.DateField(default=date.today)
    categoria = models.ForeignKey(FactorEmision, on_delete=models.PROTECT)
    peso_kg = models.DecimalField(max_digits=10, decimal_places=2)
    donante = models.CharField(max_length=200)
    observaciones = models.CharField(max_length=255, blank=True, default='')

    @property
    def co2_evitado(self):
        return float(self.peso_kg) * float(self.categoria.factor_kg_co2_por_kg)

class SimulacionDonacion(models.Model):
    FRECUENCIAS = [
        ('Unica', 'Donación Única'),
        ('Diaria', 'Diariamente (x30 días/mes)'),
        ('Semanal', 'Semanalmente (x4 semanas/mes)'),
        ('Quincenal', 'Quincenalmente (x2 al mes)'),
        ('Mensual', 'Mensualmente (x1 al mes)'),
    ]
    fecha_simulacion = models.DateField(default=date.today)
    empresa = models.CharField(max_length=200)
    categoria = models.ForeignKey(FactorEmision, on_delete=models.PROTECT)
    peso_kg = models.DecimalField(max_digits=10, decimal_places=2)
    frecuencia = models.CharField(max_length=20, choices=FRECUENCIAS, default='Unica')

    @property
    def multiplicador_mensual(self):
        mapa = {'Unica': 1, 'Diaria': 30, 'Semanal': 4, 'Quincenal': 2, 'Mensual': 1}
        return mapa.get(self.frecuencia, 1)

    @property
    def peso_proyectado_kg(self):
        return float(self.peso_kg) * self.multiplicador_mensual

    @property
    def co2_evitado_lote(self):
        return float(self.peso_kg) * float(self.categoria.factor_kg_co2_por_kg)

    @property
    def co2_evitado_proyectado(self):
        return self.peso_proyectado_kg * float(self.categoria.factor_kg_co2_por_kg)