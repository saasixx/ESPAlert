import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../config/theme.dart';

/// Education screen — what to do in each type of emergency.
class EducationScreen extends StatelessWidget {
  const EducationScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ESPAlertTheme.background,
      appBar: AppBar(title: const Text('🎓 Educación')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            '¿Qué hacer ante una emergencia?',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              color: Colors.white.withOpacity(0.9),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Guías basadas en los planes de Protección Civil',
            style: TextStyle(
              fontSize: 14,
              color: Colors.white.withOpacity(0.5),
            ),
          ),
          const SizedBox(height: 20),

          _buildGuideCard(
            emoji: '⛈️',
            title: 'Tormentas y Rayos',
            color: ESPAlertTheme.meteoColor,
            items: [
              'Busque refugio en un edificio o vehículo cerrado',
              'Aléjese de árboles aislados, postes y vallas metálicas',
              'Si está en el campo, agáchese con los pies juntos',
              'Desconecte aparatos eléctricos sensibles',
              'No use el teléfono fijo durante la tormenta',
            ],
          ),

          _buildGuideCard(
            emoji: '🌧️',
            title: 'Lluvias Intensas e Inundaciones',
            color: ESPAlertTheme.meteoColor,
            items: [
              'No cruce cauces de agua, vados o zonas inundadas',
              'No se refugie bajo puentes ni en sótanos',
              'Suba a pisos altos si el agua entra en su vivienda',
              'Tenga preparado un kit de emergencia',
              'Siga las indicaciones de Protección Civil',
            ],
          ),

          _buildGuideCard(
            emoji: '🌡️',
            title: 'Ola de Calor',
            color: ESPAlertTheme.severityOrange,
            items: [
              'Beba agua frecuentemente aunque no tenga sed',
              'Evite la exposición al sol entre 12:00 y 17:00',
              'Use ropa ligera, de colores claros y holgada',
              'Mantenga persianas y toldos cerrados durante el día',
              'Vigile especialmente a niños, mayores y enfermos crónicos',
            ],
          ),

          _buildGuideCard(
            emoji: '📳',
            title: 'Terremotos',
            color: ESPAlertTheme.seismicColor,
            items: [
              'Durante: NO salga corriendo, cúbrase bajo mesa resistente',
              'Proteja su cabeza y cuello con los brazos',
              'Aléjese de ventanas, espejos y muebles altos',
              'Después: salga con cuidado, no use ascensores',
              'Compruebe daños estructurales antes de volver a entrar',
              'Esté preparado para réplicas',
            ],
          ),

          _buildGuideCard(
            emoji: '🌊',
            title: 'Tsunami',
            color: ESPAlertTheme.maritimeColor,
            items: [
              'Si siente un terremoto fuerte cerca de la costa, evacúe inmediatamente',
              'Diríjase a zonas elevadas (30+ metros) o al interior',
              'No se acerque a la playa a observar',
              'Un tsunami puede tener varias olas durante horas',
              'Siga las indicaciones de las autoridades',
            ],
          ),

          _buildGuideCard(
            emoji: '❄️',
            title: 'Nieve, Hielo y Ola de Frío',
            color: ESPAlertTheme.meteoColor,
            items: [
              'Evite desplazamientos innecesarios',
              'Si conduce: cadenas o neumáticos de invierno',
              'Revise calefacción y tenga combustible de reserva',
              'Proteja las tuberías del congelamiento',
              'Vista en capas y proteja extremidades',
            ],
          ),

          _buildGuideCard(
            emoji: '🔥',
            title: 'Incendios Forestales',
            color: ESPAlertTheme.severityRed,
            items: [
              'Si ve humo o fuego, llame al 112 inmediatamente',
              'Evacúe en dirección contraria al viento y al humo',
              'Cierre puertas y ventanas si el fuego se acerca a su vivienda',
              'No intente apagarlo por su cuenta si es grande',
              'Nunca haga barbacoas en zonas de riesgo',
            ],
          ),

          _buildGuideCard(
            emoji: '💨',
            title: 'Viento Fuerte',
            color: ESPAlertTheme.meteoColor,
            items: [
              'Asegure toldos, macetas y objetos en balcones',
              'No se acerque a cornisas, árboles o grúas',
              'En carretera: agarre el volante con ambas manos',
              'Cuidado en puentes, salidas de túnel y zonas abiertas',
              'Cierre ventanas y persianas',
            ],
          ),

          const SizedBox(height: 40),
          Center(
            child: Text(
              'Teléfono de emergencias: 112',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w800,
                color: ESPAlertTheme.accent,
              ),
            ),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildGuideCard({
    required String emoji,
    required String title,
    required Color color,
    required List<String> items,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: ExpansionTile(
        leading: Text(emoji, style: const TextStyle(fontSize: 28)),
        title: Text(
          title,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w700,
            color: Colors.white,
          ),
        ),
        collapsedBackgroundColor: ESPAlertTheme.surfaceVariant,
        backgroundColor: ESPAlertTheme.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        collapsedShape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: items.asMap().entries.map((entry) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        margin: const EdgeInsets.only(top: 6),
                        width: 6,
                        height: 6,
                        decoration: BoxDecoration(
                          color: color,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          entry.value,
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.white.withOpacity(0.8),
                            height: 1.4,
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    ).animate().fadeIn(delay: 100.ms);
  }
}
