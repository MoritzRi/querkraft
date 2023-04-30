from PyQt5.QtWidgets import QLabel, QToolTip, QWidget
import time

groser = '\nDieser Wert muss größer als Null sein.'
groserGleich = '\nDieser Wert muss größer-gleich Null sein.'
alpha = '\nDieser Wert muss zwischen 45° und 90° liegen.'

helpTexte = {
    'Hohe' : 'Die gesamte Höhe des Querschnitts.' + groser,
    'Breite' : 'Die gesamte Breite des Querschnitts.' + groser,
    'Lange' : 'Die gesamte Länge des Balkens (von Auflagerachse zu Auflagerachse).' + groser,
    'Last' : 'Der Bemessungswert der gleichmäßigen Streckenlast, welche auf den Balken wirkt. (Eigengewicht + veränderliche Last)' + groser,
    'StatHohe' : 'Die statische Höhe des Balkens. Abstand von der Längsbewehrung zur Oberkante des Balkens.' + groser,
    'Auflagertiefe' : 'Die Breite des Auflagers (z.B. Wandstärke) auf dem der Balken aufliegt.' + groser,
    'Zugbewehrung' : 'Die gewählte Menge an Zugbewehrung im Querschnitt.' + groser,
    'Cv' : 'Die Betondeckung (bzw. Betonstärke) am Rand, in der sich keine Bewehrung befinden darf.' + groser,
    'Alpha' : 'Der Winkel der Bügelbewehrung.' + alpha,
    'Ned' : 'Die Normalkraft im Balken. Ned < 0 = Längsdruckkraft.',
    'Lagerung' : 'Es wirken günstige Druckspannungen, wenn der Balken direkt gelagert ist, also auf dem lastabtragenden Bauteil aufliegt.',
    'Fed' : 'Der Bemessungswert der optionalen Einzellast, welche ggf. auflagernah ist.' + groserGleich,
    'Av' : 'Der Abstand der Einzellast vom Auflagerrand.' + groserGleich,
    'Qed' : 'Die Querkraft mit der gerechnet werden soll.' + groser,
    'Output' : 'Entscheide wie die Berechnung exportiert werden soll.\nBei einem ausführlichen Export empfiehlt sich das HTML-Format.\nLäuft das Programm auf einem Linux- oder macOS-System? Erfahre über den Reiter "Hilfe > Hilfe" mehr über die Ausgabemöglichkeiten.'
}


def setToolTips(self):
    for key in helpTexte:
        icon = 'iconFragezeichen' + key
        try:
            label = self.findChild(QLabel, icon)
            label.setToolTip(helpTexte[key])
        except AttributeError:
            continue
        except Exception as e:
            print(e)
    