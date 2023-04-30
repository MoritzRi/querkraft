import help
import template

import sys
import numpy as np
import math
import os

from PyQt5.QtWidgets import QApplication, QMainWindow, QLineEdit, QMessageBox, QWidget
from PyQt5 import QtGui, uic
from datetime import datetime


NACHWEIS_DRUCKSTREBE = False
NACHWEIS_QUERKRAFTBEWEHRUNG = False


class Querkraft(QMainWindow):

   def __init__(self, size):
      super(Querkraft, self).__init__()
      
      # Fenster Icon setzten
      self.setWindowIcon(QtGui.QIcon(self.getPath('icon.png')))

      # Bildschirmmitte ermitteln und Fenster in Mitte setzten
      windowWidth = int(size.width() / 2)
      windowHeight = int(size.height() / 2)
      xPos = int(size.width()/2 - windowWidth/2)
      yPos = int(size.height()/2 - windowHeight/2)
      self.setGeometry(xPos, yPos, windowWidth, windowHeight)
      self.setFixedSize(windowWidth, windowHeight)
      self.setWindowTitle("Balken")

      # Lade das Startfenster
      self.loadStart()
    
      # hinterlegt fck-. fcd und pWmin-Werte
      self.fckTable = [12,16,20,25,30,35,40,45,50]
      self.fcdTable = [6.8, 9.1, 11.3, 14.2, 17, 19.8, 22.7, 25.5, 28.3]
      self.pWmin = [0.5, 0.61, 0.71, 0.82, 0.93, 1.03, 1.12, 1.21, 1.3]


   # blendet das Ergebnis aus und graut die Ausgabefunktion aus, wenn ein Parameter geändert wurde
   def hideErgebnis(self):
      self.labelErgebnis.setText('')
      self.labelErgebnis.setStyleSheet('')
      self.groupBoxOutput.setEnabled(False)
               

   # Wenn Knopf "Berechnen" im Systemfenster gedrückt wird
   def clickedSystemButton(self):      
      self.einzellastBox = self.groupBoxEinzellast.isChecked()
      print("Berechne System...\n\n")

      if not self.setValues():
         return False

      if not self.berechnenSystem():
         return False
      
      return True


   # Wenn Knopf "Berechnen" im Schnittfenster gedrückt wird
   def clickedSchnittButton(self):      
      self.einzellastBox = False
      print("Berechne Schnitt...\n\n")

      if not self.setValues():
         return False
      
      if not self.berechnenSchnitt():
         return False
      
      return True


   # Führt die Berechnung am System durch
   def berechnenSystem(self):
      # Lagerung checken
      if self.radioLagerungDirekt.isChecked():
         self.lagerungDirekt = True
      else:
         self.lagerungDirekt = False

      # alle Inputs als self.$VAR$ speichern
      self.assignInputVariables()

      # Schritt für Schritt die Berechnung durchgehen (Reihenfolge wichtig, weil einige Variablen gebraucht werden)
      self.getVedStreckenlast()
      self.getVedEinzellast()
      self.getVedAchse()
      self.getVedRand()
      self.getVedVermindert()
      
      return self.berechnung()


   # Führt die Berechnung am Schnitt durch
   def berechnenSchnitt(self):
      # Lagerung setzten, weil es beim Schnitt keine gibt
      self.lagerungDirekt = False

      # alle Inputs als self.$VAR$ speichern
      self.assignInputVariables()
      
      # einige wichtige Variablen setzten, die sonst nicht existieren
      qed = self.vars['qed']
      print(f'{qed = }')
      self.vedAchse = qed
      self.vedRand = qed
      self.vedVermindert = qed
      
      self.declareMissingVariables()

      return self.berechnung()


   # Der Teil der Berechnung, der bei System und Schnitt gleich ist
   def berechnung(self):
      # checkt das Breite zu Höhe Verhältnis
      if self.checkRatio() == False:
         return False
      # speichert die Uhrzeit für die spätere Dateibenennung
      self.timestamp = datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
      self.getSigmaCp()
      self.bewehrungErforderlich()

      # Ab hier wird die Berechnung immer min. 2-mal durchgeführt:
      # Durchmesser annehmen -> Berechnen -> Durchmesser wählen -> berechnen
      self.getHebelarm()
      self.getDruckstrebenneigung()
      self.nachweisDruckstrebe()
      self.querkraftbewehrung()
      self.getMindestbewehrung()

      self.getBuegel()
      self.checkBuegel()

      # Nachkommastellen für das Ergebnis getten
      komma = self.dropDown_2.currentIndex()
      self.showErgebnis(komma)


   # Wenn das b/h-Verhältnis zu groß ist -> Darauf hinweisen
   def checkRatio(self):
      h = self.hohe
      b = self.breite
      ratio = round(b/h, 3)

      # Warnung bei zu großem b/h Verhältnis
      if ratio >= 4:
         msg = QMessageBox()
         msg.setIcon(QMessageBox.Question)
         msg.setText('b/h = {}'.format(ratio))
         msg.setInformativeText('Das Verhältnis ist größer-gleich 4.\nDas Programm wendet Formeln für Balken an. Bei den angegeben Abmessungen kann nicht mehr von einem Balken ausgegangen werden.\nMöchtest du trotzdem fortfahren?'.format(ratio))
         msg.setWindowTitle('Achtung')
         msg.setStandardButtons(QMessageBox.No|QMessageBox.Yes)

         buttonY = msg.button(QMessageBox.Yes)
         buttonY.setText('Trotzdem berechnen')
         buttonN = msg.button(QMessageBox.No)
         buttonN.setText('Abbrechen')

         msg.exec_()

         if msg.clickedButton() == buttonY:
            return True
         elif msg.clickedButton() == buttonN:
            return False


   # Output-Datei wird hier erstellt (HTML)
   def speichernHtml(self):
      #template.createTemplate(self)
      template.generateOutputHtml(self)


   # Output-Datei wird hier erstellt (PDF)
   def speichernPdf(self):
      #template.createTemplate(self)
      template.generateOutputPdf(self)


   # Zeigt das Ergebnis an und enabled die Speicherfunktion
   def showErgebnis(self, komma = 2):
      d = self.delta[1]
      a = self.delta[2]
      s = self.delta[3]
      bewehrung = round((math.pi * (d/10 / 2)**2) / a * s, komma)

      string = ('Ergebnis:\n\n'
         	   'erf. asw:     {} cm²/m\n'
               'vorh. asw:  {} cm²/m ({}-schnittig)\n\n'
               'Bügel:         d = {} mm\n'
               'Abstand:    {} cm\n\n'
               'z/d:              {}/{} = {}').format(round(self.asw, komma), round(bewehrung, komma), s, d, round(a * 100, 1), self.z, self.statHohe, round(self.z/self.statHohe, komma+1))
      
      # Wenn keine passende Bewehrung gefunden wurde
      if self.delta[1] == 99:
         string = ('Ergebnis:\n\n'
         	   'erf. asw:     {} cm²/m\n'
               'vorh. asw:  keine passende Bewehrung\n'
               '                       gefunden!\n\n'
               'Bügel:         d = ? mm\n'
               'Abstand:    ? cm\n').format(round(self.asw, komma))

      # Wenn ein Nachweis nicht aufgegangen ist
      if NACHWEIS_QUERKRAFTBEWEHRUNG:
         string = ('\nEs ist rechnerisch keine Querkraftbewehrung erforderlich!\n'
                     'Mindestbewehrung:   {} cm²/m'.format(self.aswMin))
      if not NACHWEIS_DRUCKSTREBE:
         string = '\nDer Nachweis der Druckstrebe ist nicht aufgegangen!\nDer Querschnitt muss vergrößert werden.'

      self.labelErgebnis.setText(string)
      self.labelErgebnis.setStyleSheet('border: 1px solid red;border-radius: 5px;')
      self.groupBoxOutput.setEnabled(True)


   # Das Menu am oberen Fensterrand mit Aktionenen verknüfen
   def connectMenuBarActions(self):
      self.actionWechselnSystem.triggered.connect(self.loadSystem)
      self.actionWechselnSchnitt.triggered.connect(self.loadSchnitt)
      self.actionWechselnStart.triggered.connect(self.loadStart)
      self.actionBeenden.triggered.connect(self.close)
      self.actionInfo.triggered.connect(self.info)
      self.actionHilfe.triggered.connect(self.hilfe)


   # return den Path (Wichtig für PyInstaller)
   def getPath(self, file):
      if getattr(sys, 'frozen', False):
         path = os.path.join(sys._MEIPASS, 'res', file)
      else:
         path = os.path.join('res', file)
      return path
   

   # lade gegebene .ui Datei und setzte ToolTips
   def loadUi(self, ui):
      geo = self.geometry()
      uic.loadUi(self.getPath(ui), self)
      self.setGeometry(geo)
      self.connectMenuBarActions()
      help.setToolTips(self)


   # lade das System-Fenster
   def loadSystem(self):
      cw = self.findChild(QWidget, 'centralwidget')
      cw.setParent(None)
      self.loadUi('system.ui')
      self.fenster = 'system'
      self.inputListe = ['hohe', 'breite', 'lange', 'last', 'statHohe', 'auflagertiefe', 'zugbewehrung', 'cv', 'alpha', 'qed', 'ned', 'fed', 'av']
      self.vars = { name : 0 for name in self.inputListe}
      

   # lade das Schnitt-Fenster
   def loadSchnitt(self):
      cw = self.findChild(QWidget, 'centralwidget')
      cw.setParent(None)
      self.loadUi('schnitt.ui')
      self.fenster = 'schnitt'
      self.inputListe = ['hohe', 'breite', 'lange', 'last', 'statHohe', 'auflagertiefe', 'zugbewehrung', 'cv', 'alpha', 'qed', 'ned', 'fed', 'av']
      self.vars = { name : 0 for name in self.inputListe}


   # lade das Start-Fenster
   def loadStart(self):
      self.loadUi('start.ui')
      self.fenster = 'start'
      

   # zeige kleines Infofenster ("Hilfe > Über...")
   def info(self):
      msgInfo = QMessageBox()
      msgInfo.setIcon(QMessageBox.Information)
      msgInfo.setText('Balken')
      msgInfo.setInformativeText('Open Source Tool zu berechnung der Querkraftbewehrung\n\nMoritz Rieger - 2023')
      msgInfo.setWindowTitle('Über...')
      msgInfo.exec_()

   # zeige kleines Hilfefenster mit Inhalt der README Datei("Hilfe > Hilfe")
   def hilfe(self):
      file = open(self.getPath('README.txt'), 'r', encoding='utf-8')
      data = file.read()
      msgHilfe = QMessageBox()
      msgHilfe.setIcon(QMessageBox.Information)
      msgHilfe.setText('Information:')
      msgHilfe.setInformativeText(data)
      msgHilfe.setWindowTitle('Info')
      msgHilfe.exec_()


   # Entertaste handlen um eine schnellere Eingabe zu ermöglichen
   def enter(self):
      # Das fokusierte Wisget getten
      name = self.focusWidget().objectName()
      index = self.inputListe.index(name)

      anzahlInputs = len(self.inputListe)

      # Wenn Einzellast nicht ausgewählt ist -> SKIP
      if self.fenster == 'schnitt' or not self.groupBoxEinzellast.isChecked():
         anzahlInputs -= 2

      # Wenn es nicht das letzte Feld ist -> zun nächsten (aus Inputliste)
      if index + 1 < anzahlInputs:
         input = self.findChild(QLineEdit, self.inputListe[index + 1])
      
      # Beim letzten Feld -> Berechnung starten
      else:
         if self.fenster == 'system':
            self.clickedSystemButton()
         if self.fenster == 'schnitt':
            self.clickedSchnittButton()
         input = self.findChild(QLineEdit, self.inputListe[0])

      # Wenn es das nächste Widget nicht gibt -> Übernächstes
      i = 1
      while input == None:
         i += 1
         input = self.findChild(QLineEdit, self.inputListe[index + i])

      # Fokus setzten und Text markieren
      input.setFocus()
      input.selectAll()
  

   # Sobald berechnen gedrückt wurde -> Eingabewerte in das Value-Dictionary schreiben
   def setValues(self):
      # Für jeden Wert durchgehen und Fokus setzen
      for key in self.vars:
         inputBox = self.findChild(QLineEdit, key)

         # Wenn er den Input nicht finden kann -> nächster Input
         if inputBox == None:
            continue

         inputBox.setFocus()

         # Versuche in Float zu konvertieren
         try:
            input = float(inputBox.text().replace(',', '.'))

            # Wenn der Input nicht valide ist (z.B. Text) -> Error raisen
            if self.validate(inputBox.text()) == False:
               raise ValueError('To be catched...')

            # Wenn alles klappt -> als Input setzen
            self.vars[key] = input

         # Wenn es nicht geht -> Fenster anzeigen: "Eingabe überprüfen"
         except ValueError:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText('Achtung!')
            msg.setInformativeText('Eingabe überprüfen')
            msg.setWindowTitle('Fehler')
            msg.exec_()
            return False
         except:
            Warning("Fatal Error bei 'setValue()'")
            return False
         
      if self.einzellastBox == False:
         self.vars['fed'] = 0
         self.vars['av'] = 0

      return True


   # Checkt ob Eingabe legitim ist, wenn der Input verändert wird
   def validate(self, input):
      self.hideErgebnis()
      name = self.focusWidget().objectName()

      # LEER -> WEIß
      if input == '':
          self.focusWidget().setStyleSheet("background-color: white")
          return False

      try:
         input = float(input.replace(',', '.'))

         # Diese Inputs dürfen auch Null sein
         if name == 'fed' or name == 'av': #or name == 'ned':

            # ZAHL größer-gleich 0 -> VALIDE
            if input >= 0:
               self.focusWidget().setStyleSheet("background-color: white")
            else:
               self.focusWidget().setStyleSheet("background-color: red")
               return False

         # Alpha darf nur zwischen 45 und 90 Grad betragen
         elif name == 'alpha':
            if input >=45 and input <= 90:
               self.focusWidget().setStyleSheet("background-color: white")
            else:
               self.focusWidget().setStyleSheet("background-color: red")
               return False
            
         # Ned darf auch negativ sein
         elif name == 'ned':
            self.focusWidget().setStyleSheet("background-color: white")
            
         else:
            # ZAHL größer 0 -> VALIDE
            if input > 0:
               self.focusWidget().setStyleSheet("background-color: white")
            else:
               self.focusWidget().setStyleSheet("background-color: red")
               return False

      # KEINE ZAHL         
      except ValueError:
         self.focusWidget().setStyleSheet("background-color: red")
         return False
      # FATAL
      except:
         Warning("Fatal Error bei 'validate()' mit '{}'".format(name))
         return False


   # Berechnet VedStreckenlast (Auflagerachse)
   def getVedStreckenlast(self):
      l = self.lange
      p = self.last

      self.vedStreckenlast = p * l / 2

      print('\n##### getVedStreckenlast #####')
      print(f'{   self.vedStreckenlast = }')

      return self.vedStreckenlast


   # Berechnet VedEinzellast (Auflagerachse)
   def getVedEinzellast(self):
      l = self.lange
      fed = self.fed
      auflagertiefe = self.auflagertiefe / 100
      av = self.vars['av'] / 100

      self.b = l - auflagertiefe/2 - av
      faktor = self.b / l
      self.vedEinzellast = faktor * fed

      print('\n##### getVedEinzellast #####')
      print(f'{   self.b = }')
      print(f'{   faktor = }')
      print(f'{   self.vedEinzellast = }')

      return self.vedEinzellast


   # berechnet Ved (Auflagerachse)
   def getVedAchse(self):
      #vedStreckenlast = self.getVedStreckenlast()
      #vedEinzellast = self.getVedEinzellast()
      self.vedAchse = self.vedStreckenlast + self.vedEinzellast
      
      print('\n##### getVedAchse #####')
      print(f'{   self.vedAchse = }')

      return (self.vedAchse)


   # Berechnet Ved (Auflagerand)
   def getVedRand(self):
      auflagertiefe = self.auflagertiefe / 100
      p = self.last

      self.xAuflager = auflagertiefe / 2
      self.vedRand = self.vedStreckenlast - p * self.xAuflager + self.vedEinzellast

      print('\n##### getVedRand #####')
      print(f'{   self.vedRand = }')

      return self.vedRand


   # berechnet Ved vermindert
   def getVedVermindert(self):
      # WIRD NUR BEI DIREKTER LAGERUNG VERWENDET!
      # Lade Parameter
      auflagertiefe = self.auflagertiefe / 100
      b = self.breite / 100
      av = self.av / 100
      p = self.last
      fcd = self.fcdTable[self.dropDown.currentIndex()]
      d = self.statHohe / 100
 
      self.vedEinzellastGrenze = 0.3375 * b * d * fcd * 1000
      self.xVermin = auflagertiefe / 2 + d
      self.vedStreckenlastVermindert = self.vedStreckenlast - p * self.xVermin

      if av < 2*d and av >= 0.5*d:
         self.beta = av / (2 * d)
      elif av < 0.5*d:
         self.beta = 0.25
      else:
         self.beta = 1
      
      if self.vedEinzellastGrenze < self.vedEinzellast:
         self.vedEinzellastVermindert = self.vedEinzellast
      else:
         self.vedEinzellastVermindert = self.beta * self.vedEinzellast

      self.vedVermindert = self.vedStreckenlastVermindert + self.vedEinzellastVermindert

      print('\n##### getVedVermindert #####')
      print(f'{   self.beta = }')
      print(f'{   self.vedStreckenlastVermindert = }')
      print(f'{   self.vedEinzellastGrenze = }')
      print(f'{   self.vedEinzellastVermindert = }')
      print(f'{   self.vedVermindert = }')

      return self.vedVermindert


   # SigmaCP berechnen
   def getSigmaCp(self):
      # Lade Parameter
      b = self.breite * 10  # mm
      h = self.hohe * 10    # mm
      ned = self.ned * -1000 # N
      self.fcd = self.fcdTable[self.dropDown.currentIndex()]

      self.sigmaCpTmp = ned / (b * h)

      self.sigmaCP = min(self.sigmaCpTmp, 0.2 * self.fcd)

      print('\n##### getSigmaCP #####')
      print(f'{   self.sigmaCpTmp = }')
      print(f'{   self.sigmaCP = }')
      print(f'{   self.fcd = }')

      return self.sigmaCP


   # Querkraftbewehrung erforderlich? (Ved < VRd,c)
   def bewehrungErforderlich(self):
      # Lade Parameter
      global NACHWEIS_QUERKRAFTBEWEHRUNG
      d = self.statHohe * 10  # mm
      b = self.breite * 10    # mm
      zugbewehrung = self.zugbewehrung * 100   # mm²

      # Berechne vRdc
      self.k = min(1 + np.sqrt(200 / d),2)
      
      self.langsbewehrungsgrad = min(zugbewehrung / (b * d),0.02)
      
      fck = self.fckTable[self.dropDown.currentIndex()]

      self.vRdcTmp = (( 0.1 * self.k * (100 * self.langsbewehrungsgrad * fck)**(1/3) + 0.12 * self.sigmaCP ) * b * d) / 1000     # kN

      # vRdc größer Grenzwert?
      self.vMin = 0
      self.vMin600 = 0.035 * self.k**(3/2) * fck**(1/2)
      self.vMin800 = 0.025 * self.k**(3/2) * fck**(1/2)

      if d <= 600:
         self.vMin = self.vMin600
      if d > 800:
         self.vMin = self.vMin800
      else:
         self.vMin = np.interp(d, [600, 800], [self.vMin600, self.vMin800])

      self.vRdcGrenze = (self.vMin + 0.12 * self.sigmaCP) * b * d / 1000
      
      self.vRdc = max(self.vRdcTmp, self.vRdcGrenze)

      # VedVermindert oder Achse?
      if self.lagerungDirekt:
         vedGesamt = self.vedVermindert
      else:
         vedGesamt = self.vedAchse

      print('\n##### Querkraftbewehrung erforderlich? (Ved < VRd,c) ######')
      print(f'{   self.k = }')
      print(f'{   self.langsbewehrungsgrad = }')
      print(f'{   self.sigmaCP = }')
      print(f'{   fck = }')
      print(f'{   self.vRdcTmp = }')
      print(f'{   self.vMin600 = }')
      print(f'{   self.vMin800 = }')
      print(f'{   self.vMin = }')
      print(f'{   self.vRdc = }')
      print(f'{   vedGesamt = }')

      if vedGesamt > self.vRdc:
         NACHWEIS_QUERKRAFTBEWEHRUNG = False
         return False
      else:
         NACHWEIS_QUERKRAFTBEWEHRUNG = True
         return True

  
   # Brechnet die Druckstrebeneigung 
   def getDruckstrebenneigung(self):
      # Lade Parameter
      b = self.breite * 10 # mm
      fck = self.fckTable[self.dropDown.currentIndex()]
      fcd = self.fcdTable[self.dropDown.currentIndex()]
      ned = self.ned
      
      self.vRdcc = 0.24 * fck**(1/3) * (1 - 1.2 * (self.sigmaCpTmp/fcd)) * b * self.z * 10 / 1000 # kN
      
      if self.lagerungDirekt:
         ved = self.vedVermindert
      else:
         ved = self.vedAchse
      
      self.cot0 = (1.2 + 1.4 * self.sigmaCpTmp / fcd) / (1 - self.vRdcc / ved)

      if self.cot0 < 1:
         self.cot0 = 1
      if self.cot0 > 3:
         self.cot0 = 3
      
      print('\n##### Berechnung der Druckstrebenneigung #####')
      print(f'{   self.vRdcc = }')
      print(f'{   ved = }')
      print(f'{   self.cot0 = }')

      return self.cot0


   # Drucksrebe nachweisen Ved << VRd,max 
   def nachweisDruckstrebe(self):
      # Lade Parameter
      global NACHWEIS_DRUCKSTREBE
      self.COT_VERMINDERT = 0
      b = self.breite * 10 # mm
      z = self.z * 10  # mm
      alpha = self.alpha
      fcd = self.fcdTable[self.dropDown.currentIndex()]
      self.cot0Vermindert = 0

      if self.lagerungDirekt:
         ved = self.vedRand
      else:
         ved = self.vedAchse

      self.theta = math.atan(1/self.cot0) * 180 / math.pi
      cotAlpha = self.cot(alpha)
      
      self.vRdMax = b * z * 0.75 * fcd * ( (self.cot0 + cotAlpha) / (1 + self.cot0**2)) / 1000  # Kn

      if ved <= self.vRdMax:
         NACHWEIS_DRUCKSTREBE = True

      elif ved > self.vRdMax:
         c = b * z * 0.75 * fcd
         self.cot0Vermindert = (c + np.sqrt(c**2 + 4000 * cotAlpha * c * ved - 4000000 * ved**2)) / (2000*ved)

         if self.cot0Vermindert >= 1:
            self.vRdMax = b * z * 0.75 * fcd * ( (self.cot0Vermindert + cotAlpha) / (1 + self.cot0Vermindert**2)) / 1000  # Kn
            self.cot0 = self.cot0Vermindert
            self.COT_VERMINDERT = 1
            NACHWEIS_DRUCKSTREBE = True
         else:
            self.cot0Vermindert = 1
            self.cot0 = self.cot0Vermindert
            self.COT_VERMINDERT = 2
            NACHWEIS_DRUCKSTREBE = False

      print('\n###### Nachweis der Druckstrebe #####')
      print(f'{   self.theta = }')
      print(f'{   alpha = }')
      print(f'{   cotAlpha = }')
      print(f'{   ved = }')
      print(f'{   self.cot0Vermindert = }')
      print(f'{   self.vRdMax = }')


   # Ermittlung der erforderilchen Querkraftbewehrung (Bewehrung orthogonal zur Achse)
   def querkraftbewehrung(self):
      # Lade Parameter
      z = self.z / 100 # m

      if self.lagerungDirekt:
         ved = self.vedVermindert
      else:
         ved = self.vedAchse

      self.asw = ved / (43.5 * z * (self.cot0 + self.cot(self.alpha)) * np.sin(self.rad(self.alpha)))

      print('\n##### Berechung der Querkraftbewehrung #####')
      print(f'{   self.alpha = }')
      print(f'{   self.asw = }')

      return self.asw


   # Ermittlung der erfordelichen Mindestbewehrung asw,min
   def getMindestbewehrung(self):
      # Lade Parameter
      self.rhoW = self.pWmin[self.dropDown.currentIndex()]
      b = self.vars['breite'] * 10 # mm
      alpha = self.vars['alpha'] * np.pi / 180  # Rad

      self.aswMin = self.rhoW/1000 * b * np.sin(alpha) * 10

      print('\n##### erforderliche Mindestbewehrung #####')
      print(f'{   self.aswMin = }')

      return self.aswMin
   

   # setzt die Bewehrungsvariable self.delta[diff erf/vorh, durchmesser, Abstand, Schnittigkeit]
   def getBuegel(self):
      # Lade Parameter
      schnittig = [ 2, 4]
      abstaende = [ 5, 6, 7, 7.5, 8, 9, 10, 12.5, 15, 20, 25 ]
      durchmesser = [ 6, 8, 10, 12, 14, 16 ]

      self.delta = [999, 99, 99, 99]

      # guckt ob die Mindestbewehrung ggf. maßgeben ist
      asw = self.asw
      if self.aswMin > self.asw:
         asw = self.aswMin

      # Geht alle Möglichkeiten Von Durchmessern und Abständen durch
      for s in schnittig:
         for d in durchmesser:
            for a in abstaende:

               # Bei überschreitung der Grenze -> überspringen
               if a > self.maxBuegelAbstand():
                  continue

               # Bei 4-schnittiger Bewehrung -> keine Durhcmesser 6 und 8mm Stäbe
               if s == 4 and (d == 6 or d == 8):
                  continue

               # Ermittelt Differenz aus erf. und mögl. Bewehrung
               a = a / 100
               bewehrungsmenge = (self.flaeche(d) * s / a)
               deltaTmp = bewehrungsmenge - asw

               # speichert immer die kleinste mögl. Bewehrung, die größer ist als erf. asw
               if deltaTmp >= 0 and deltaTmp < self.delta[0]:
                  self.delta = [deltaTmp, d, a, s]

      # Wenn das nicht geklappt hat -> aufgeben         
      if self.delta[0] == 999:
         print('Es konnte keine passende Bewehrung gewählt werden.')
         return False
      
      print('\n#### Wahl der Bewehrung ####')
      print('  Durchmesser = {} mm'.format(self.delta[1]))
      print('  Abstand = {} cm'.format(self.delta[2]))

      return self.delta
   

   # Checken, ob die Berechnung noch aufgeht mit neuen Bügeln -> neues cvl -> neues z
   def checkBuegel(self):
      # aufgeben, wenn kein passender Bügel gefunden wurde
      if not self.getBuegel():
         return
      print('\nChecke Bügel d = {} mm mit Abstand {} cm ({}-schnittig)...'.format(self.delta[1], round(self.delta[2]*100, 1), self.delta[3]))
      self.getHebelarm(self.delta[1])
      self.getDruckstrebenneigung()
      self.nachweisDruckstrebe()
      self.querkraftbewehrung()

      bewehrungBuegel = (round(self.flaeche(self.delta[1]) * self.delta[3] / self.delta[2], 3))
   
      if not NACHWEIS_QUERKRAFTBEWEHRUNG and NACHWEIS_DRUCKSTREBE:
         # Printe und return, wenn es aufgeht
         if self.asw < bewehrungBuegel:
            print('\nBügel d = {} mm mit Abstand {} cm ({}-schnittig: {}cm²/m) passen!'.format(self.delta[1],  round(self.delta[2]*100, 1), self.delta[3], bewehrungBuegel))
            return True
         
         # Weiter versuchen mit neuem Bügel
         else:
            self.getBuegel()
            self.checkBuegel()
      else:
         if NACHWEIS_QUERKRAFTBEWEHRUNG:
            print('\nEs ist rechnerisch keine Querkraftbewehrung erforderlich!')
         if not NACHWEIS_DRUCKSTREBE:
            print('\nDer Nachweis der Druckstrebe ist nciht aufgegangen! Der Querschnitt muss vergrößert werden.')


   # ermittelt den maximal erlaubten Bügelabstand
   def maxBuegelAbstand(self):
      if self.vedAchse > 0.6*self.vRdMax:
         self.maxAbstand = min(0.25 * self.hohe, 20)
      elif self.vedAchse < 0.3*self.vRdMax:
         self.maxAbstand = min(0.7 * self.hohe, 30)
      else:
         self.maxAbstand = min(0.5 * self.hohe, 30)

      return self.maxAbstand


   # Fläche eines Kreises
   def flaeche(self, durchmesser):
      return math.pi * (durchmesser/10 / 2)**2


   # Hebelarm der inneren Kräfte vereinfacht berechnen
   def getHebelarm(self, buegeldurchmesser = 10):
      # Lade Parameter
      self.cvl = self.cv + buegeldurchmesser / 10
      d = self.statHohe # cm

      self.zTmp = 0.9 * d
      self.zGrenze = max(d - self.cvl - 3, d - 2 * self.cvl)  # cm
      self.z = min(self.zTmp, self.zGrenze)

      print('\n##### Berechnung des inneren Hebelarms #####')
      print(f'{   self.z = }')
      print(f'{   buegeldurchmesser = }')
      return self.z


   # Cotangens berechnen
   def cot(self, deg):
      return np.cos(self.rad(deg))/np.sin(self.rad(deg))
   

   # deg in rad umrechnen
   def rad(self, deg):
      return deg * np.pi / 180
   

   # Input in Variablen schreiben
   def assignInputVariables(self):
      self.hohe = self.vars['hohe']
      self.breite  = self.vars['breite']
      self.lange  = self.vars['lange']
      self.last  = self.vars['last']
      self.statHohe  = self.vars['statHohe']
      self.auflagertiefe  = self.vars['auflagertiefe']
      self.zugbewehrung  = self.vars['zugbewehrung']
      self.cv  = self.vars['cv']
      self.alpha  = self.vars['alpha']
      self.qed  = self.vars['qed']
      self.ned  = self.vars['ned']
      self.fed  = self.vars['fed']
      self.av  = self.vars['av']
   

   # fehlende Variablen declaren, die beim Schnitt sonst fehlen würden
   def declareMissingVariables(self):
      self.vedStreckenlast  = 0
      self.vedStreckenlastVermindert  = 0
      self.vedEinzellast  = 0
      self.vedEinzellastVermindert  = 0
      self.b  = 0
      self.xAuflager  = 0
      self.xVermin  = 0
      self.beta  = 0


def window():
   app = QApplication(sys.argv)
   screen = app.primaryScreen()
   win = Querkraft(screen.size())

   # setzte das Fenster Design
   app.setStyle('Fusion')
   # app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
   win.show()
   sys.exit(app.exec_())


if __name__ == '__main__':
   window()
