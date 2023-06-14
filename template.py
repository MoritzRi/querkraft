import math
import numpy as np
import os
import platform

import sys
import shutil
import pdfkit

from PyQt5.QtWidgets import QFileDialog, QMessageBox
from math import atan, pi


RUNDUNG = 3
INDENT = 40
NACHWEIS = False

sizeEinheiten = 8 # Größe der Einheiten
sizeKlammern = 35 # Größe der Klammern '{}' und '[]'

CURLAUF = '&#123'
CURLZU = '&#125'
KLEINERGLEICH = ' &#8804 '
BLITZ = ' &#8623 '
HAKEN = ' &#10004 '


RHO = '&#961 '
SIGMA = '&#963 '
NU = '&#957 '
THETA = '&#920'
ALPHA = '&#945'
BETHA = '&#946'


# return den Path (Wichtig für PyInstaller)
def getPath(file, subDir = 'res'):
    if getattr(sys, 'frozen', False):
        path = os.path.join(sys._MEIPASS, subDir, file)
    else:
        path = os.path.join(subDir, file)
    return path


# erstellt einen Bruch in CSS
def frac(varU, varD):
    return '<div class="frac"><span>{}</span>'.format(str(varU)) + '<span class="symbol">/</span> ' + '<span class="bottom">{}</span> '.format(str(varD)) + '</div>'


# erstellt einen etwas kleineren Bruch un CSS (für die Einheiten)
def fracSmall(varU, varD):
    return '<div class="fracSmall"><span>{}</span>'.format(str(varU)) + '<span class="symbol">/</span> ' + '<span class="bottom">{}</span> '.format(str(varD)) + '</div>'
      

# stellt tiefer in CSS
def sub(var1, var2):
    return str(var1) + '<span class = "sub">' +str(var2) + '</span> '


# macht die sub Funktion wieder Rückgängig (um die wahre anzahl an Zeichen zählen zu können)
def rmSub(string):
    return string.replace('<span class = "sub">', '').replace('</span>', '')


# Stellt hoch in CSS
def sup(var1, var2):
    return str(var1) + '<span class = "sup">' +str(var2) + '</span> '


# Wurzel von num
def root(num):
    return '<span style="white-space: nowrap; font-size:larger">\n&radic;<span style="text-decoration:overline;">&nbsp;' + num + '&nbsp;</span>\n</span>\n'


# Macht den String größer
def gross(string, num):
    return '<span style="font-size: {}px;">'.format(num) + string + '</span>'


# erstellt Min-Gleichung
def min(var1, var2):
    return 'min {} {} '.format(gross(CURLAUF, sizeKlammern), var1) + gross(',', sizeKlammern * .8) + ' {} {}'.format(var2, gross(CURLZU, sizeKlammern))


# erstellt Max-Gleichung
def max(var1, var2):
    return 'max {}  {} '.format(gross(CURLAUF, sizeKlammern), var1) + gross(',', sizeKlammern * .8) + ' {} {}'.format(var2, gross(CURLZU, sizeKlammern))


# fügt richtige Menge an Leerzeichen an String, um bestimmte Zeilen zu alignen
def fixLength(string, length):
        l = len(rmSub(str(string)))
        return str(string) + ' ' * (length - l)


# erstellt den HTML-Code für einen Titel
def titel(string, count = 0):
     return  '<hr>\n<h2 style="margin-left: {}px;margin-bottom: 10px" id="{}"><u>'.format(count*INDENT, string) + string + '</u></h2>\n\n'


# erstellt den HTML-Code für eine Zeile Text
def lineRaw(text, count = 1):
    html = '<span style="margin-left: {}px;margin-bottom: 30px;margin-top: 30px">{}</span><br><br>\n'
    html = html.format(count*INDENT, text.replace('\n', '<br>'))
    return html


# erstellt den HTML-Code für die aufklappbaren bulletpoints
def itemize(symbol, beschreibung, einheit):
    if einheit != '':
        return '    <li>{}  : {} in {}</li>\n'.format(symbol, beschreibung, einheit)
    else:
        return '    <li>{}  : {} (einheitslos)</li>\n'.format(symbol, beschreibung)


# erstellt den HTML-Code für den Anfang der aufklappbaren Bulletpoints ("mit: ...")
def openMit(count = 3):
    return '\n' + '<p style="margin: 5px 5px 0px {}px">'.format(count*INDENT) + '<font size="2">mit:</font></p>\n' + '<ul style="margin-left: {}px;margin-top: 0px">\n'.format(count*INDENT)


# schließt die Bulletpoint-Liste wieder
def closeMit():
    return '</ul>\n'


# öffnet die Details (aufklappbare Formel)
def openDetails(titel, count = 2):
    return '<details style="margin-left: {}px">\n'.format(count*INDENT) + '<summary>' + titel + '</summary>\n'


# schließst die Details wieder
def closeDetails():
    return '</details><br><br>\n'


# erstellt den HTML-Code für die Berechnung (Formel, Werte, Ergebnis, Details)
def rechnung(formel, vars, count = 2):
    string = '<details style="margin-left: {}px">\n'.format(count*INDENT) + '<summary>'
    names = unpackDict(namen, vars)
    werte = unpackDict(zwischenwerte, vars)
    for i,v in enumerate(vars):
        werte[i] = str(werte[i]) + ' ' + einheiten[v]
    
    #string += '{} = '.format(names[0]) + rmMathAdvanced(formel.format(*names[1:])) + formel.format(*werte[1:]) + str(werte[0]) + ''+einheiten[vars[0]] + '</summary>\n'
    string += '{} = '.format(names[0]) + formel.format(*names[1:]) + formel.format(*werte[1:]) + str(werte[0]) + '</summary>\n'
    
    string += mit(vars[1:])
    string += closeDetails()
    return string


# erstellt den HTML-Code für die Berechnung (Variable und Wert)
def rechnungKurz(var, count = 1):
    string = '<span style="margin-left: {}px">\n'.format(count*INDENT)
    string += '{} = {} {}</span><br><br>\n'.format(namen[var], round(zwischenwerte[var], RUNDUNG), einheiten[var])
    return string


# erstellt den HTML-Code für die Nachweise
def nachweis(ed, rd):
    global NACHWEIS
    string = '<span id="nachweis">\n'
    numEd = round(zwischenwerte[ed], RUNDUNG)
    numRd = round(zwischenwerte[rd], RUNDUNG)
    ratio = round(numEd / numRd, RUNDUNG)
    #string += frac(rmMath(namen[ed]), rmMath(namen[rd])) + ' = ' + frac(numEd, numRd) + ' = ' + gross(str(ratio), 20)
    string += frac(namen[ed], namen[rd]) + ' = ' + frac(numEd, numRd) + ' = ' + gross(str(ratio), 20)

    if ratio <= 1:
        string += gross(KLEINERGLEICH + ' 1    ' + HAKEN, 28) + '<br>Damit ist der Nachweis erfüllt.'
        NACHWEIS = True
    else:
        string += gross(' > 1  ' + BLITZ, 28) + '<br>Damit ist der Nachweis <b>nicht</b> erfüllt.'
        NACHWEIS = False

    return string + '\n </span>'


# erstellt den HTML-Code für Bulletpoint-Liste
def mit(vars, count = 1):
    stringMit = openMit(count)
    #vars = set(vars).values()
    for item in set(vars):
        stringMit += itemize(namen[item], beschreibungen[item], einheiten[item])
    stringMit += closeMit()
    return stringMit


# nimmt die Variablen aus dem Dictionary und returnt eine Liste
def unpackDict(dict, vars):
    names = []
    for item in vars:
        if type(dict[item]) == int or type(dict[item]) == float or type(dict[item]) == np.float64:
            names.append(round(dict[item], RUNDUNG))
        else:
            names.append(dict[item])
    return names


# checkt, ob Werte keinen Wert haben oder unendlich sind
def checkValues():
    infList = []
    nanList = []

    for key in zwischenwerte:
        if zwischenwerte[key] == float('inf') or zwischenwerte[key] == float('-inf'):
            infList.append(key)
        if zwischenwerte[key] != zwischenwerte[key]:
            nanList.append(key)
    
    # return, wenn alle Werte OK sind
    if not infList and not nanList:
        return
    
    # Zeigt Fehlermeldung, wenn nicht alle Werte OK sind
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Question)
    msg.setText('Unerwartete Werte')

    text = ''
    for elem in infList:
        text += elem + ' = inf\n'

    for elem in nanList:
        text += elem + ' = NaN\n'

    msg.setInformativeText('Einige Werte sind unendlich und/oder konnten nicht berechnet werden\n' + text + '\nDas Programm könnte bei der Ausgabe abstürzen. Soll die Berechnung trotzdem ausgegeben werden?')
    msg.setWindowTitle('Achtung')
    msg.setStandardButtons(QMessageBox.No|QMessageBox.Yes)

    buttonY = msg.button(QMessageBox.Yes)
    buttonY.setText('Trotzdem ausgeben')
    buttonN = msg.button(QMessageBox.No)
    buttonN.setText('Abbrechen')

    msg.exec_()

    if msg.clickedButton() == buttonY:
        return True
    elif msg.clickedButton() == buttonN:
        return False


# wird vom Hauptprogramm aufgerufen, wenn exportiert werden soll
def createTemplate(self):
    global s
    global RUNDUNG
    global output

    s = self

    RUNDUNG = s.dropDown_2.currentIndex()

    # lädt alle Informationen zu den Variablen
    createData()

    # checkt, ob Werte keinen Wert haben oder unendlich sind
    if checkValues() == False:
        return False
    
    # Ausführlicher Output
    if s.radioButtonAusfuhrlich.isChecked():
        print('\nOutput: ausführlich')
        output = 'ausführlich'
        createTemplateAusfuhrlich()

    # Kurzer Output
    else:
        print('\nOutput: kurz')
        output = 'kurz'
        createTemplateKurz()


# speichert die .html Datei ab
def generateOutputHtml(self):
    # Wenn die angegebendnen Querkräfte gleich sind, wird von einer indirekten Lagerung ausgegangen
    if self.fenster == 'schnitt' and self.vedRand == self.vedVermindert:
        self.lagerungDirekt = False
    
    if createTemplate(self) == False:
        return False
    
    global output
    global s
    
    outputFileName = 'Berechung_{}({}).html'.format(s.timestamp, output)
    #outputFileName = output + '.html'
    src = getPath('output.html')
    dst = save(outputFileName, "HTML (*.html)")

    if dst != None:
        shutil.copy(src, dst)


# speichert die .pdf Datei ab
def generateOutputPdf(self):
    # Wenn die angegebendnen Querkräfte gleich sind, wird von einer indirekten Lagerung ausgegangen
    if self.fenster == 'schnitt' and self.vedRand == self.vedVermindert:
        self.lagerungDirekt = False

    if createTemplate(self) == False:
        return False
    

    # checkt das Betriebssystem und weist darauf hin, dass momentan nur Windows den PDF-Export unterstützt
    if platform.system() != "Windows":
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText('PDF-Output nicht möglich')
        msg.setInformativeText('Momentan unterstützt nur Windows das Exportieren als PDF-Datei. Die HTML-Ausgabe kann jedoch im Browser deiner Wahl als PDF abgespeichert werden.')
        msg.setWindowTitle('Fehler')
        msg.setStandardButtons(QMessageBox.Ok)
        buttonO = msg.button(QMessageBox.Ok)
        buttonO.setText('Ok')

        msg.exec_()

        if msg.clickedButton() == buttonO:
            return True
            
    global output
    global s
    
    outputFileName = 'Berechung_{}({}).pdf'.format(s.timestamp, output)
    #outputFileName = output + '.pdf'
    src = getPath('output.html')
    dst = save(outputFileName, "PDF (*.pdf)")

    if dst != None:
        try:
            options = {'page-size':'A3'}
            wkhtmltopdfPath = getPath('wkhtmltopdf.exe')
            config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdfPath)
            pdfkit.from_file(src, output_path=dst, configuration=config, options = options)
        except:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText('Speichern fehlgeschlagen')
            msg.setInformativeText('Die Datei konnte nicht gespeichtert werden. Ist eine Datei mit gleichem Namen bereits geöffnet?')
            msg.setWindowTitle('Fehler')
            msg.setStandardButtons(QMessageBox.Ok)
            buttonO = msg.button(QMessageBox.Ok)
            buttonO.setText('schließen')

            msg.exec_()

            if msg.clickedButton() == buttonO:
                return True


# zeigt ein Dialogfenster, um die Datei zu speichern
def save(outputFile, format="Alle Dateien(*.*)"):
    filePath, _ = QFileDialog.getSaveFileName(s, "Berechnung speichern...", outputFile, format)

    # abbrechen, falls kein Name angegeben wurde
    if filePath == "":
        return

    return filePath


# Hier wird der kurze output erstellt
def createTemplateKurz():
    # alle globalen Variablen verfügbar machen
    global s
    global namen
    global zwischenwerte
    global einheiten
    global beschreibungen
    global RUNDUNG
    global eingabeparameterSystem
    global eingabeparameterSchnitt

    # HTML-Vorlage öffnen und Rechenweg einfügen
    with open(getPath('template.html'), 'r') as f:
        templateString = f.read()

        templateString = templateString.replace('%plch0%', setAusgabe())

        templateString = templateString.replace('%plch1%', setEingabe())

        if s.fenster == 'system':
            templateString = templateString.replace('%plch2%', setVedsSystemKurz())
        else:
            templateString = templateString.replace('%plch2%', setVedsSchnittKurz())

        templateString = templateString.replace('%plch3%', bewehrungErforderlichKurz())

        if NACHWEIS:
            bs = lineRaw('Berechnung zu Ende!')
            templateString = templateString.replace('%plch4%', bs)
            templateString = templateString.replace('%plch5%', '')
            templateString = templateString.replace('%plch6%', '')
            templateString = templateString.replace('%plch7%', mindestbewehrungKurz(True))
            templateString = templateString.replace('%plch8%', '')
            write(templateString)
            return

        templateString = templateString.replace('%plch4%', druckstrebenneigungKurz())

        templateString = templateString.replace('%plch5%', nachweisDruckstrebeKurz())
        if not NACHWEIS:
            bs = lineRaw('Berechnung zu Ende!')
            templateString = templateString.replace('%plch6%', bs)
            templateString = templateString.replace('%plch7%', '')
            templateString = templateString.replace('%plch8%', '')
            write(templateString)
            return

        templateString = templateString.replace('%plch6%', bewehrungKurz())
        templateString = templateString.replace('%plch7%', mindestbewehrungKurz())
        templateString = templateString.replace('%plch8%', bewehrungswahlKurz())

    write(templateString)
    return


# Hier wird der kurze output erstellt
def createTemplateAusfuhrlich():
    # alle globalen Variablen verfügbar machen
    global s
    global namen
    global zwischenwerte
    global einheiten
    global beschreibungen
    global RUNDUNG
    global eingabeparameterSystem
    global eingabeparameterSchnitt
    global ausgabeparameterSystem
    global ausgabeparameterSchnitt

    # HTML-Vorlage öffnen und Rechenweg einfügen
    with open(getPath('template.html'), 'r') as f:
        templateString = f.read()

        templateString = templateString.replace('%plch0%', setAusgabe())

        templateString = templateString.replace('%plch1%', setEingabe())

        if s.fenster == 'system':
            templateString = templateString.replace('%plch2%', setVedsSystem())
        else:
            templateString = templateString.replace('%plch2%', setVedsSchnitt())

        templateString = templateString.replace('%plch3%', bewehrungErforderlich())

        if NACHWEIS:
            bs = lineRaw('Berechnung zu Ende!')
            templateString = templateString.replace('%plch4%', bs)
            templateString = templateString.replace('%plch5%', '')
            templateString = templateString.replace('%plch6%', '')
            templateString = templateString.replace('%plch7%', mindestbewehrung(True))
            templateString = templateString.replace('%plch8%', '')
            write(templateString)
            return

        templateString = templateString.replace('%plch4%', druckstrebenneigung())

        templateString = templateString.replace('%plch5%', nachweisDruckstrebe())
        if not NACHWEIS:
            bs = lineRaw('Berechnung zu Ende!')
            templateString = templateString.replace('%plch6%', bs)
            templateString = templateString.replace('%plch7%', '')
            templateString = templateString.replace('%plch8%', '')
            write(templateString)
            return

        templateString = templateString.replace('%plch6%', bewehrung())
        templateString = templateString.replace('%plch7%', mindestbewehrung())
        templateString = templateString.replace('%plch8%', bewehrungswahl())

    write(templateString)


# schreibt einen String in eine Datei
def write(str):
    with open(getPath('output.html'), 'w') as f:
        f.write(str)


# erstellt den HTML-Code für die Eingabeparameter
def setEingabe():
    if s.fenster == 'system':
        dict = eingabeparameterSystem
    else:
        dict = eingabeparameterSchnitt

    eingabeString = '<pre style="margin: 5px;padding: 0px">\n'
    for key in dict:
           eingabeString += dict[key].format(eval('s.' + key)) + '<br>\n'

    return eingabeString + '</pre>\n'


# erstellt den HTML-Code für die Ausgabeparameter
def setAusgabe():
    if s.fenster == 'system':
        list = ausgabeparameterSystem
    else:
        list = ausgabeparameterSchnitt

    eingabeString = '<pre style="margin: 5px;padding: 0px">\n'
    for var in list:
        eingabeString += fixLength(namen[var], 10) + '= {} {}<br>\n'.format(fixLength(round(zwischenwerte[var], RUNDUNG), 8), einheiten[var])

    for key in ausgabeparameter:
        sonderzeichen = ['rho', 'cot0', 'sigmaCp', 'sigmaCd', 'pWmin']
        spaces = 10
        if key in sonderzeichen:
            spaces = 14
        eingabeString += fixLength(namen[key], spaces) + '= {} {}<br>\n'.format(fixLength(round(zwischenwerte[key], RUNDUNG), 8), ausgabeparameter[key])

    return eingabeString + '</pre>\n'


# erstellt den HTML-Code für Berechnung der Querkräfte am System(kurz)
def setVedsSystemKurz():
    bs = titel('1) Querkräfte berechnen')

    bs += rechnungKurz('vedStreckenlast')
    bs += rechnungKurz('vedEinzellast')
    bs += rechnungKurz('vedAchse')
    bs += rechnungKurz('vedRand')

    if s.lagerungDirekt == True:
        bs += lineRaw('Lagerung direkt -> Querkraft vermindern')
        bs += rechnungKurz('vedStreckenlastVermindert')

        if s.vedEinzellastGrenze < s.vedEinzellast:
            bs += lineRaw('Die Einzellast ist zu groß, um abgemindert zu werden.')
        elif s.vedEinzellast == 0:
            bs += ''
        elif s.beta != 1:
            bs += lineRaw('Einzellast ist auflagernah -> vermindern')
            bs += rechnungKurz('vedEinzellastVermindert')
        else:
            bs += lineRaw('Einzellast ist nicht auflagernah -> nicht vermindern')

    else:
        bs += lineRaw('Lagerung indirekt -> Querkraft nicht vermindern')
    return bs


# erstellt den HTML-Code für Berechnung der Querkräfte am System (lang)
def setVedsSystem():
   # bs = '\n<h2>Querkräfte berechnen</h2>\n'

    bs = titel('1) Querkräfte berechnen')
    bs += rechnung(frac('{} · {}','2') + ' = ', ['vedStreckenlast', 'p', 'L'])
    bs += rechnung(frac('{}','{}') + '· {} = ', ['vedEinzellast', 'bVed', 'L', 'fed']) 
    bs += rechnung('{} + {} = ', ['vedAchse', 'vedStreckenlast', 'vedEinzellast'])
    bs += rechnung('{} - {} · {} + {} = ', ['vedRand', 'vedStreckenlast', 'p', 'xAuflager', 'vedEinzellast'])

    if s.lagerungDirekt == True:
        bs += lineRaw('Auf Grund der direkten Lagerung und der gleichmäßigen Streckenlast kann die daraus resuktierende Querkraft wie folgt vermindert werden:')
        bs += rechnung('{} - {} · {} = ', ['vedStreckenlastVermindert', 'vedStreckenlast', 'p', 'xVermin'])
        bs += lineRaw('Die Querkraft an der Stelle x (statische Höhe d vom Auflagerrand entfernt) ist somit die verminderte Querkraft infolge der Streckenlast.')

        av = zwischenwerte['av']
        d = zwischenwerte['d']

        if s.vedEinzellastGrenze < s.vedEinzellast:
            bs += lineRaw('Allerdings ist die Einzellast in diesem Fall zu groß, um abgemindert zu werden, da sie den Grenzwert')
            bs += lineRaw('{} {} 0,3375 · {} · {} · {}'.format(namen['ved'], KLEINERGLEICH, namen['breite'], namen['d'], namen['fcd']), 2)
            bs += lineRaw('überschreitet.')

        elif s.vedEinzellast == 0:
            bs += lineRaw('Es wurde keine auflagernahe Einzellast angegeben.\n')

        elif av < 2*d and av > 0.5*d:
            bs += lineRaw('Da die auflagernahe Einzellast weniger als 2 d vom Auflagerrand entfernt ist, darf die Querkraft mit dem Faktor:\n')
            bs += rechnung(frac('{}', '2 · {}') + ' =',['beta', 'av', 'd'])
            bs += lineRaw('abgemindert werden. Also beträgt die abgeminderte Querkraft infolge der Einzellast:')
            bs += rechnung('{} · {} = ', ['vedEinzellastVermindert', 'beta', 'fed'])

        elif av < 0.5*d:
            bs += lineRaw('Da die auflagernahe Einzellast weniger als 0.5 d vom Auflagerrand entfernt ist, darf die Querkraft mit dem Faktor:\n')
            bs += rechnungKurz('beta', 2)
            bs += lineRaw('abgemindert werden.\nAlso beträgt die abgeminderte Querkraft infolge der Einzellast:')
            bs += rechnung('{} · {} = ', ['vedEinzellastVermindert', 'beta', 'fed'])
            

        else:
            bs += lineRaw('Da die auflagernahe Einzellast mehr als 2 d vom Auflagerrand entfert ist, darf die Querkraft nicht abgemindert werden.\n')
        
        bs += lineRaw('Somit beläuft sich die abgeminderte Querkraft auf:')
        bs += rechnung('{} + {} = ', ['vedVermindert', 'vedStreckenlastVermindert', 'vedEinzellastVermindert'])
        
    else:
        bs += lineRaw('Auf Grund der indirekten Lagerung kann die Querkraft nicht abgemindert werden.\n')

    bs += lineRaw('Damit ist die berechnung aller erforderlichen Querkräfte abgeschlossen.\n')
    return bs


# erstellt den HTML-Code für Berechnung der Querkräfte am Schnitt (kurz)
def setVedsSchnittKurz():
    bs = titel('1) Querkräfte berechnen')

    if s.lagerungDirekt == True:
        bs += lineRaw('Lagerung direkt -> Querkräfte gegeben')
        bs += rechnungKurz('vedVermindert')
        bs += rechnungKurz('vedRand')

    else:
        bs += lineRaw('Lagerung indirekt -> Querkraft gegeben:')
        bs += rechnungKurz('ved')

    return bs


# erstellt den HTML-Code für Berechnung der Querkräfte am Schnitt (lang)
def setVedsSchnitt():
    bs = titel('1) Querkräfte berechnen')

    if s.lagerungDirekt == True:
        bs += lineRaw('Lagerung direkt -> Querkräfte gegeben')
        bs += lineRaw('{} = {} {} (gegeben)'.format(namen['vedRand'], str(round(zwischenwerte['vedRand'], RUNDUNG)), einheiten['vedRand']))
        bs += lineRaw('{} = {} {} (gegeben)'.format(namen['vedVermindert'], str(round(zwischenwerte['vedVermindert'], RUNDUNG)), einheiten['vedVermindert']))

    else:
        bs += lineRaw('Lagerung indirekt -> Querkraft gegeben:')
        bs += lineRaw('{} = {} {} (gegeben)'.format(namen['ved'], str(round(zwischenwerte['ved'], RUNDUNG)), einheiten['ved']))

    return bs


# erstellt den HTML-Code für den Nachweis: Querkraftbewerung erforderlich? (kurz)
def bewehrungErforderlichKurz():
    bs = titel('2) Querkraftbewehrung erforderlich?')

    bs += rechnungKurz('k')
    bs += rechnungKurz('rho')
    bs += rechnungKurz('fck')
    bs += rechnungKurz('fcd')
    bs += rechnungKurz('sigmaCp')
    bs += rechnungKurz('vMin')
    bs += rechnungKurz('vRdc')
    
    if s.lagerungDirekt:
        bs += lineRaw('Lagerung direkt -> verminderte Querkraft für Nachweis')
        bs += nachweis('vedVermindert', 'vRdc')
    elif not s.lagerungDirekt:
        bs += lineRaw('Lagerung indirekt -> Querkraft in der Auflagerachse für Nachweis')
        bs += nachweis('vedAchse', 'vRdc')
    
    if not NACHWEIS:
        bs += lineRaw('Somit ist rechnerisch eine Querkraftbewehrung erforderlich.')
    else:
        bs += lineRaw('Somit ist rechnerisch keine Querkraftbewehrung erforderlich.')

    return bs


# erstellt den HTML-Code für den Nachweis: Querkraftbewerung erforderlich? (lang)
def bewehrungErforderlich():
    bs = titel('2) Querkraftbewehrung erforderlich?')

    bs += lineRaw('Zunächst werden alle erforderlichen Parameter berechnet, beginnend mit dem Maßstabsfaktor k:')
    bs += rechnung(min('1 + ' + root('200 / {}'), '2') + ' = ', ['k', 'd'])

    bs += lineRaw('Der Längsbewehrungsgrad ' + sub(RHO, 'l') + ' wird wie folgt berechnet:')
    bs += rechnung(min(frac('{}', '{} · {}'), '0.02') + ' = ', ['rho', 'zugbewehrung', 'breite', 'd'])

    bs += lineRaw('Der charakteristische Wert der Betondruckfestigkeit ({}) und der Bemessungswert der Betondruckfestigkeit ({}) bei einem {} Beton betragen:'.format(namen['fck'], namen['fcd'], namen['beton']))
    bs += lineRaw('{} = {} {}'.format(namen['fck'], zwischenwerte['fck'], einheiten['fck']), 2)
    bs += lineRaw('{} = {} {}'.format(namen['fcd'], zwischenwerte['fcd'], einheiten['fcd']), 2)

    bs += lineRaw('Anschließend kann der Bemessungswert der Betonlängsspannung ({}) berechnet werden.'.format(namen['sigmaCp']))
    bs += rechnung(min(frac('{} · 1000', '{}'), '0.2 · {}') + ' = ', ['sigmaCp', 'ned', 'ac', 'fcd'])

    bs += lineRaw('In Querschnitten ist rechnerisch keine Querkraftbewehrung erforderlich, wenn die Bedingung \'{} {} {}\' erfüllt ist.'.format(sub('V', 'Ed'), KLEINERGLEICH, namen['vRdcTmp']))
    bs += lineRaw('Mit den obenstehenden Werten kann nun {} berechnet werden.'.format(namen['vRdcTmp']))
    bs += rechnung(gross('[', sizeKlammern) + '0.1 · {} · ' + sup('(100 · {} · {})', '1/3') + ' + 0.12 · {}' + gross(']', sizeKlammern) + ' · {} · {} ÷ 1000= ', ['vRdcTmp', 'k', 'rho', 'fck', 'sigmaCp', 'breite', 'd'])
    bs += lineRaw('Allerdings gibt es folgende untere Grenze für {}, welche nicht unterschritten werden darf:'.format(namen['vRdcTmp']))
    bs += lineRaw('[{} + 0.12 · {}] · {} · {} ÷ 10'.format(namen['vMin'], namen['sigmaCp'], namen['breite'], namen['d']), 2)
    bs += lineRaw('Dabei wird {} abhängig von der statischen Höhe {} berechnet:'.format(namen['vMin'], namen['d']))
    bs += rechnung('0.035 · ' + sup( '{}', '3/2') + ' · ' + sup('({})', '1/2') + ' = ', ['vMin600', 'k', 'fck'])
    bs += rechnung('0.025 · ' + sup( '{}', '3/2') + ' · ' + sup('({})', '1/2') + ' = ', ['vMin800', 'k', 'fck'])

    if zwischenwerte['d'] > 600 and zwischenwerte['d'] <= 800:
        bs += lineRaw('Da die statische Höhe {} zwischen 600 und 800 mm liegt, wird der Wert für {} linear interpoliert.'.format(namen['d'], namen['vMin']))
    
    bs += lineRaw('Somit ist {} = {} und die untere Grenze für {} beträgt:'.format(namen['vMin'], round(zwischenwerte['vMin'], RUNDUNG), namen['vRdcTmp']))
    bs += lineRaw('[{} + 0.12 · {}] · {} · {} = {} {} = {} {}'.format(round(zwischenwerte['vMin'], RUNDUNG), round(zwischenwerte['sigmaCp'], RUNDUNG), round(zwischenwerte['breite'], RUNDUNG), round(zwischenwerte['d'], RUNDUNG), round(s.vRdcGrenze * 1000, RUNDUNG), 'N', round(s.vRdcGrenze, RUNDUNG), 'kN'), 2)

    if zwischenwerte['vRdcTmp'] < s.vRdcGrenze:
        bs += lineRaw('Da {} mit {} {} kleiner ist, wird der Grenzwert für den Nachweis verwendet.'.format(namen['vRdcTmp'], round(zwischenwerte['vRdcTmp'], RUNDUNG), einheiten['vRdcTmp']))
    else:
        bs += lineRaw('Da {} mit {} {} größer ist, kann der Wert für den Nachweis herangezogen werden.'.format(namen['vRdcTmp'], round(zwischenwerte['vRdcTmp'], RUNDUNG), einheiten['vRdcTmp']))

    if s.lagerungDirekt:
        bs += lineRaw('Da die Lagerung direkt ist, kann für diesen Nachweis die verminderte Querkraft angesetzt werden:')
        bs += nachweis('vedVermindert', 'vRdc')
    elif not s.lagerungDirekt:
        bs += lineRaw('Da die Lagerung indirekt ist, muss für diesen Nachweis die Querkraft in der Auflagerachse angesetzt werden:')
        bs += nachweis('vedAchse', 'vRdc')

    if not NACHWEIS:
        bs += lineRaw('Somit ist rechnerisch eine Querkraftbewehrung erforderlich.')
    else:
        bs += lineRaw('Somit ist rechnerisch keine Querkraftbewehrung erforderlich.')
    
    return bs


# erstellt den HTML-Code für die Berechnung der Druckstrebenneigung (kurz)
def druckstrebenneigungKurz():
    COT_VERMINDERT = s.COT_VERMINDERT

    bs = titel('3) Berechnung der Druckstrebenneigung')

    if COT_VERMINDERT == 0:
        bs += rechnungKurz('z')
        bs += rechnungKurz('vRdcc')
        bs += rechnungKurz('cot0')
        bs += rechnungKurz('theta')
    
    elif COT_VERMINDERT == 1:
        bs += lineRaw('Ein kleieres {} muss gewählt werden, damit der Nachweis aufgehen kann.'.format(namen['cot0']))
        bs += rechnungKurz('cot0', 2)

    elif COT_VERMINDERT == 2:
        bs += lineRaw('Untere Grenze für {} von 1,0 wurde gewählt.'.format(namen['cot0']))
        bs += rechnungKurz('cot0', 2)

    return bs


# erstellt den HTML-Code für die Berechnung der Druckstrebenneigung (lang)
def druckstrebenneigung():
    COT_VERMINDERT = s.COT_VERMINDERT

    bs = titel('3) Berechnung der Druckstrebenneigung')
    bs += lineRaw('Um den Nachweis der Druckstrebe führen zu können, benötigt man zunächst die Druckstrebenneigung {}.'.format(THETA))
    bs += lineRaw('Der Kotangens dieses Winkels ist wie folgt begrenzt:')
    bs += lineRaw(('1.0 ' + KLEINERGLEICH + ' {} ' + KLEINERGLEICH + frac('1.2 + 1.4 · {} / {}', '1 - {} / {}') + ' < 3.0').format(namen['cot0'], namen['sigmaCp'], namen['fcd'], namen['vRdcc'], namen['vedRand']), 2)
        
    if COT_VERMINDERT == 0:
        bs += lineRaw('Um ein wirtschaftliches Ergebnis zu erzielen, wird für {} die obere Grenze gewählt.'.format(namen['cot0']))

        bs += lineRaw('Um {} berechnen zu können, wird zusätzlich der innere Hebelarm ermittelt (vereinfachte Methode):'.format(namen['vRdcc']))
        bs += rechnung('0.9 · {} = ', ['zTmp', 'd'])
        bs += lineRaw('Dabei ist zu beachten, dass der Wert durch')
        bs += rechnung(max('{} - {} - 30', '{} - 20 · {}') + ' = ', ['zGrenze', 'd', 'cv', 'd', 'cv'])
        bs += lineRaw('begrenzt wird. Somit gilt:')
        bs += lineRaw('{} = {} {}'.format(namen['z'], round(zwischenwerte['z'], RUNDUNG), einheiten['z']), 3)

        bs += lineRaw('Im nächsten Schritt kann nun {} berechnet werden.'.format(namen['vRdcc']))
        bs += rechnung('0.24 · ' + sup('{}', '1/3') + ' · (1 - 1.2 · ' + frac('{}', '{}') + ') · {} · {} ÷ 1000 = ', ['vRdcc', 'fck', 'sigmaCd', 'fcd', 'breite', 'z'])

        if s.lagerungDirekt:
            ved = 'vedVermindert'
        else:
            ved = 'vedAchse'

        bs += lineRaw('Daraus ergibt sich ein {} von:'.format(namen['cot0']))
        bs += rechnung(frac('1.2 + 1.4 · {} ÷ {}', '1 - {} ÷ {}') + ' = ', ['cot0', 'sigmaCd', 'fcd', 'vRdcc', ved])
        if zwischenwerte['cot0'] == 1 or zwischenwerte['cot0'] == 3:
            bs += lineRaw('(begrenzt durch die oben genannten Grenzen)', 3)
        if zwischenwerte[ved] < zwischenwerte['vRdcc']:
            bs += lineRaw('Da {} kleiner als {} ist, kann die obere Grenze für {} von 3,0 gewählt werden.'.format(namen['ved'], namen['vRdcc'], namen['cot0']))

    elif COT_VERMINDERT == 1:
        bs += lineRaw('Damit der Nachweis der Druckstrebe aufgeht, wird für {} der Wert'.format(namen['cot0']))
        bs += rechnungKurz('cot0', 2)
        bs += lineRaw('gewählt.')

    elif COT_VERMINDERT == 2:
        bs += lineRaw('Um {} zu maximieren, wird für {} der Wert'.format(namen['vRdMax'], namen['cot0']))
        bs += rechnungKurz('cot0', 2)
        bs += lineRaw('gewählt.')
    
    bs += lineRaw('Somit ist die Druckstrebe um {} ° geneigt.'.format(round(zwischenwerte['theta'], RUNDUNG)))

    return bs


# erstellt den HTML-Code für den Nachweis der Druckstrebe (kurz)
def nachweisDruckstrebeKurz():
    bs = titel('4) Nachweis der Druckstrebe')

    bs += rechnungKurz('vRdMax')

    if s.lagerungDirekt:
        ved = 'vedRand'
    elif  not s.lagerungDirekt:
        ved = 'vedAchse'

    bs += nachweis(ved, 'vRdMax')
    if NACHWEIS:
        bs += lineRaw('Somit kann die Druckstrebe die auftretenden Druckspannungen aufnehmen.')
    else:
        bs += lineRaw('Somit kann die Druckstrebe - auch mit einem {} = 1 - die auftretenden Druckspannungen nicht aufnehmen. Der Querschnitt muss vergrößert werden.'.format(namen['cot0']))

    return bs


# erstellt den HTML-Code für den Nachweis der Druckstrebe (lang)
def nachweisDruckstrebe():
    bs = titel('4) Nachweis der Druckstrebe')

    bs += lineRaw('Um ein Versagen des Bauteils auf Grund zu hoher Druckspannungen zu vermeiden, muss sichergestellt werden, dass diese Grenze eingehalten ist.')
    bs += lineRaw('Alle dafür erforderlichen Größen wurden im Verlauf der vorherigen Berechnungen bereits ermittelt. Somit ergibt sich ein {} von:'.format(namen['vRdMax']))
    bs += rechnung('{} · {} · 0.75 · {} · ' + frac('{} + cot({})', '1 + ' + sup('{}', '2')) + ' ÷ 1000 = ', ['vRdMax', 'breite', 'z', 'fcd', 'cot0', 'alpha', 'cot0'])

    if s.lagerungDirekt:
        bs += lineRaw('Dieser Wert kann nun der Querkraft am Auflagerrand (direkte Lagerung) gegenübergestellt werden:')
        bs += nachweis('vedRand', 'vRdMax')
    elif s.fenster == 'system' and not s.lagerungDirekt:
        bs += lineRaw('Dieser Wert kann nun der Querkraft in der Auflagerachse (indirekte Lagerung) gegenübergestellt werden:')
        bs += nachweis('vedAchse', 'vRdMax')
    else:
        bs += lineRaw('Dieser Wert kann nun der Querkraft gegenübergestellt werden:')
        bs += nachweis('ved', 'vRdMax')

    if NACHWEIS:
        bs += lineRaw('Somit kann die Druckstrebe die auftretenden Druckspannungen aufnehmen.')
    else:
        bs += lineRaw('Somit kann die Druckstrebe - auch mit einem {} = 1 - die auftretenden Druckspannungen nicht aufnehmen. Der Querschnitt muss vergrößert werden.'.format(namen['cot0']))
    return bs


# erstellt den HTML-Code für die Berechnung der Querkraftbewehrung (kurz)
def bewehrungKurz():
    bs = titel('5) Ermittlung der erforderlichen Querkraftbewehrung')

    bs += lineRaw('{} = {} {}'.format(namen['fywd'], zwischenwerte['fywd'], einheiten['fywd']), 1)

    if not s.lagerungDirekt:
        bs += lineRaw('Lagerung indirekt -> Querkraft an Auflagerachse')
    elif s.lagerungDirekt:
        bs += lineRaw('Lagerung direkt -> verminderte Querkraft')

    bs += rechnungKurz('asw')
    return bs


# erstellt den HTML-Code für die Berechnung der Querkraftbewehrung (lang)
def bewehrung():
    bs = titel('5) Ermittlung der erforderlichen Querkraftbewehrung')

    bs += lineRaw('Die Querkraftbewehrung wird so gewählt, dass der Zuggurt maximal ausgelastet ist. Dadurch wird eine effiziente Bewehrungsmenge gewährleistet.')
    bs += lineRaw('Die letzte fehlende Angabe ist die Streckgrenze das Bewehrungsstahls {}:'.format(namen['fywd']))

    bs += lineRaw('{} = {} {}'.format(namen['fywd'], zwischenwerte['fywd'], einheiten['fywd']), 2)

    ved = 'ved'
    if s.lagerungDirekt:
        bs += lineRaw('Da der Balken direkt gelagert ist, kann für die Querkraft der verminderte Wert angesetzt werden.')
        ved = 'vedVermindert'
    elif not s.lagerungDirekt:
        bs += lineRaw('Da der Balken indirekt gelagert ist, muss für die Querkraft der Wert in der Auflagerachse angesetzt werden.')
        ved = 'vedAchse'
    
    bs += lineRaw('Nun kann die erforderliche Querkraftbewehrung nach folgender Formel berechnet werden:')
    bs += rechnung(frac('{} · 1000', '{} · {} · [{} + cot({})] · sin({})') + ' · 10 = ', ['asw', ved, 'fywd', 'z', 'cot0', 'alpha', 'alpha'])
    return bs


# erstellt den HTML-Code für die Berechnung der Mindestquerkraftbewehrung (kurz)
def mindestbewehrungKurz(massgebend = False):
    bs = titel('6) Einhalten der Mindestbewehrung')

    bs += lineRaw(namen['beton'])
    bs += rechnungKurz('pWmin')
    bs += rechnungKurz('aswMin')

    if massgebend:
        bs += lineRaw('Da rechnerisch keine Querkraftbewehrung erforderlich ist, ist die Mindestquerkraftbewehrung maßgebend.')
        return bs

    if zwischenwerte['asw'] > zwischenwerte['aswMin']:
        bs += lineRaw('Somit ist diese Grenze eingehalten.')
    else:
        bs += lineRaw('Somit ist diese Grenze nicht eingehalten und die Mindestquerkraftbewehrung ist maßgebend.')
    return bs


# erstellt den HTML-Code für die Berechnung der Mindestquerkraftbewehrung (lang)
def mindestbewehrung(massgebend = False):
    bs = titel('6) Einhalten der Mindestbewehrung')

    bs += lineRaw(namen['beton'])

    if massgebend:
        bs += rechnung('{} · {} · sin({}) · 10 = ', ['aswMin', 'pWmin', 'breite', 'alpha'])
        bs += lineRaw('Da rechnerisch keine Querkraftbewehrung erforderlich ist, ist die Mindestquerkraftbewehrung maßgebend.')
        return bs
    
    bs += lineRaw('Um im Balken die erforderliche Mindestbewehrung einzuhalten, muss geprüft werden, ob die rechnerisch erforderliche Bewehrung ausreicht.')
    bs += lineRaw('Für die Berechnung der Mindestbewehrung muss zunnächst der Mindestbewehrungsgrad {} bekannt sein.'.format(namen['pWmin']))
    bs += lineRaw('Dieser ist vom charakteristischen Mittelwert der Betonzugfestigkeit abhängig und beträgt bei einem {}:'.format(namen['beton']))
    bs += lineRaw('{} = {} {}'.format(namen['pWmin'], zwischenwerte['pWmin'], einheiten['pWmin']), 2)
    bs += lineRaw('Nun kann nach folgender Formel die Mindestquerkraftbewehrung berechnet werden:')
    bs += rechnung('{} · {} · sin({}) · 10 = ', ['aswMin', 'pWmin', 'breite', 'alpha'])

    if zwischenwerte['asw'] > zwischenwerte['aswMin']:
        bs += lineRaw('Somit ist diese Grenze eingehalten.')
    else:
        bs += lineRaw('Somit ist diese Grenze nicht eingehalten und die Mindestquerkraftbewehrung ist maßgebend.')
    return bs


# erstellt den HTML-Code für die Wahl der Querkraftbewehrung (kurz)
def bewehrungswahlKurz():
    global s
    bs = titel('7) Wahl der Bewehrung')

    if zwischenwerte['delta'][1] == 99:
        bs += lineRaw('Es konnte keine passende Bewehrung gewählt werden.')
        return bs
    
    ved = zwischenwerte['ved']
    vRdMax = zwischenwerte['vRdMax']

    if s.fenster == 'schnitt' and s.lagerungDirekt == True:
        bs += lineRaw('Da die Lagerung direkt ist und keine Querkraft in Auflagerachse gegeben ist, wird der maximale Bügelabstand auf der sicheren Seite liegend auf {} {} gesetzt.'.format(zwischenwerte['maxAbstand'], einheiten['maxAbstand']))
    elif ved <= 0.3 * vRdMax:
        bs += lineRaw('{} {} 0.3 · {} => {} = {} {}'.format(namen['ved'], KLEINERGLEICH, namen['vRdMax'], namen['maxAbstand'], zwischenwerte['maxAbstand'], einheiten['maxAbstand']))
    elif ved > 0.6 * vRdMax:
        bs += lineRaw('{} > 0.6 · {}  => {} = {} {}'.format(namen['ved'], namen['vRdMax'], namen['maxAbstand'], zwischenwerte['maxAbstand'], einheiten['maxAbstand']))
    else:
        bs += lineRaw('0.3 · {} {} {} {} 0.6 · {}  => {} = {} {}'.format(namen['vRdMax'], KLEINERGLEICH, namen['ved'], KLEINERGLEICH, namen['vRdMax'], namen['maxAbstand'], zwischenwerte['maxAbstand'], einheiten['maxAbstand']))
    
    d = zwischenwerte['delta'][1]
    a = zwischenwerte['delta'][2]
    schnittig = zwischenwerte['delta'][3]
    bewehrung = round((math.pi * (d/10 / 2)**2) / a * 2, RUNDUNG)


    bs += lineRaw('Gewählte Bügelbewehrung ({}-schnittig):'.format(schnittig))
    bs += lineRaw('Durchmesser: {} mm'.format(d), 2)
    bs += lineRaw('Abstand: {} cm'.format(a*100), 2)
    bs += lineRaw('Vorhandene Bewehung: {}'.format(bewehrung) + frac('cm²', 'm'), 2)

    bs += lineRaw('Berechnung zu Ende.')
    return bs


# erstellt den HTML-Code für die Wahl der Querkraftbewehrung (lang)
def bewehrungswahl():
    bs = titel('7) Wahl der Bewehrung')

    if zwischenwerte['delta'][1] == 99:
        bs += lineRaw('Es konnte keine passende Bewehrung gewählt werden.')
        return bs
    
    bs += lineRaw('Bei der Wahl der Bewehrung gibt es viele richtige Ansätze. Dieses Programm bietet lediglich eine effiziente Bewehrungsmege, um Stahl zu sparen.')
    bs += lineRaw('Das einzige, das hierbei beachtet werden muss, ist der maximale Abstand der Bügel.')
    

    ved = zwischenwerte['ved']
    vRdMax = zwischenwerte['vRdMax']

    if s.fenster == 'schnitt' and s.lagerungDirekt == True:
        bs += lineRaw('Da die Lagerung direkt ist und keine Querkraft in Auflagerachse gegeben ist, wird der maximale Bügelabstand auf der sicheren Seite liegend auf {} {} gesetzt.'.format(zwischenwerte['maxAbstand'], einheiten['maxAbstand']))
    
    elif ved <= 0.3 * vRdMax:
        bs += lineRaw('Dieser ist von der Ausnutzung des Zuggurts abhängig und beträgt in diesem Fall:')
        bs += lineRaw(('Für {} {} 0.3 · {} :      ' + min('0.7 · h', '30cm') + ' = {}cm').format(namen['ved'], KLEINERGLEICH, namen['vRdMax'], zwischenwerte['maxAbstand']), 2)
    elif ved > 0.6 * vRdMax:
        bs += lineRaw('Dieser ist von der Ausnutzung des Zuggurts abhängig und beträgt in diesem Fall:')
        bs += lineRaw(('Für {} > 0.6 · {} :      ' + min('0.25 · h', '20cm') + ' = {}cm').format(namen['ved'], namen['vRdMax'], zwischenwerte['maxAbstand']), 2)
    else:
        bs += lineRaw('Dieser ist von der Ausnutzung des Zuggurts abhängig und beträgt in diesem Fall:')
        bs += lineRaw(('Für 0.3 · {} {} {} {} 0.6 · {} :      ' + min('0.5 · h', '30cm') + ' = {}cm').format(namen['vRdMax'], KLEINERGLEICH, namen['ved'], KLEINERGLEICH, namen['vRdMax'], zwischenwerte['maxAbstand']), 2)
        
    d = zwischenwerte['delta'][1]
    a = zwischenwerte['delta'][2]
    schnittig = zwischenwerte['delta'][3]
    bewehrung = round((math.pi * (d/10 / 2)**2) / a * 2, RUNDUNG)

    bs += lineRaw('Demnach wäre eine passende Bügelbewehrung:')
    bs += lineRaw('Durchmesser: {} mm'.format(d), 2)
    bs += lineRaw('Abstand: {} cm'.format(a*100), 2)
    bs += lineRaw('Vorhandene Bewehung ({}-schnittig): {}'.format(schnittig, bewehrung) + fracSmall('cm²', 'm'), 2)

    bs += lineRaw('Berechnung zu Ende.')
    return bs


# Hier werden alle nötigen Informationen der Variablen deklariert
# Eine eigene Klasse wür die Variablen zu schreiben wäre wesentlich besser, leider keine Zeit mehr
# ToDo -> Klasse für Variablen schreiben
def createData():
    # Lädt die globalen Variablen
    global namen
    global zwischenwerte
    global einheiten
    global beschreibungen
    global eingabeparameterSystem
    global eingabeparameterSchnitt
    global ausgabeparameterSystem
    global ausgabeparameterSchnitt
    global ausgabeparameter
    global s

    # Deklariert die Variablennamen (z.B. Symbole, tiefer gestellt, etc.)
    namen = {   'ved' : sub('V', 'Ed'),
                'beton' : s.dropDown.currentText(),
                'vedStreckenlast' : sub('V', 'Ed,Streckenlast'),
                'p' : 'p',
                'L' : 'L',
                'vedEinzellast' : sub('V', 'Ed,Einzellast'),
                'bVed' : 'b',
                'fed' : sub('F', 'Ed'),
                'vedAchse' : sub('V', 'Ed,Achse'),
                'vedRand' : sub('V', 'Ed,Rand'),
                'xAuflager' : 'x',
                'vedStreckenlastVermindert' : sub('V', 'Ed,Streckenlast,vermindert'),
                'xVermin' : 'x',
                'beta' : BETHA,
                'av' : sub('a', 'v'),
                'd' : 'd',
                'vedEinzellastVermindert' : sub('V', 'Ed,Einzellast,vermindert'),
                'fed' : sub('F', 'Ed'),
                'vedVermindert' : sub('V', 'Ed,Vermindert'),
                'k' : 'k',
                'rho' : sub(RHO, 'l'),
                'zugbewehrung': sub('A', 'sl'),
                'breite' : sub('b', 'w'),
                'fck' : sub('f', 'ck'),
                'fcd' : sub('f', 'cd'),
                'sigmaCp' : sub(SIGMA, 'cp'),
                'ned' : sub('N', 'Ed'),
                'ac' : sub('A', 'c'),
                'vRdcTmp' : sub('V', 'Rd,c'),
                'vMin' : sub(NU, 'min'),
                'vMin600' : 'Für d {} 600mm :'.format( KLEINERGLEICH),
                'vMin800' : 'Für d > 800mm :',
                'vRdc' : sub('V', 'Rd,c'),
                'cot0' : 'cot(' + THETA + ')',
                'theta' : THETA,
                'vRdcc' : sub('V', 'Rd,cc'),
                'zTmp' : 'z',
                'z' : 'z',
                'zGrenze' : 'obere Grenze für z:',
                'cv' : sub('c', 'vl'),
                'sigmaCd' : sub(SIGMA, 'cd'),
                'vRdMax' : sub('V', 'Rd,max'),
                'alpha' : ALPHA,
                'fywd' : sub('f', 'ywd'),
                'asw' : sub('a', 'sw'),
                'aswMin' : sub('a', 'sw,min'),
                'pWmin' : sub(RHO, 'w,min'),
                'maxAbstand' : 'maximaler Abstand',
                'delta' : 'gewählte Bewehrung'
    } 

    # Deklariert die Variablewerte
    zwischenwerte = {   'ved' : s.vedAchse,
                        'beton' : 0,
                        'vedStreckenlast' : s.vedStreckenlast,
                        'p' : s.last,
                        'L' : s.lange,
                        'vedEinzellast' : s.vedEinzellast,
                        'bVed' : s.b,
                        'fed' : s.fed,
                        'vedAchse' : s.vedAchse,
                        'vedRand' : s.vedRand,
                        'xAuflager' : s.xAuflager,
                        'vedStreckenlastVermindert' : s.vedStreckenlastVermindert,
                        'xVermin' : s.xVermin,
                        'beta' : s.beta,
                        'av' : s.av * 10,
                        'd' : s.statHohe * 10,
                        'vedEinzellastVermindert' : s.vedEinzellastVermindert,
                        'fed' : s.fed,
                        'vedVermindert' : s.vedVermindert,
                        'k' : float(s.k),
                        'rho': s.langsbewehrungsgrad,
                        'zugbewehrung': s.zugbewehrung * 100,
                        'breite': s.breite * 10,
                        'fck' : s.fckTable[s.dropDown.currentIndex()],
                        'fcd' : s.fcdTable[s.dropDown.currentIndex()],
                        'sigmaCp' : s.sigmaCP,
                        'ned' : -1 * s.ned,
                        'ac' : s.breite * s.hohe * 100,
                        'vRdcTmp' : float(s.vRdcTmp),
                        'vMin' : float(s.vMin),
                        'vMin600' : float(s.vMin600),
                        'vMin800' : float(s.vMin800),
                        'vRdc' : float(s.vRdc),
                        'cot0' : s.cot0,
                        'theta' : s.theta,
                        'vRdcc' : s.vRdcc,
                        'zTmp' : s.zTmp,
                        'z' : s.z * 10,
                        'zGrenze' : s.zGrenze * 10,
                        'cv' : s.cvl * 10,
                        'sigmaCd' : s.sigmaCpTmp,
                        'vRdMax' : float(s.vRdMax),
                        'alpha' : s.alpha,
                        'fywd' : 435,
                        'asw' : s.asw,
                        'aswMin' : s.aswMin,
                        'pWmin' : s.rhoW,
                        'maxAbstand' : s.maxAbstand,
                        'delta' : s.delta
    }

    # Deklariert die Variableneinheiten
    einheiten = {       'ved' : 'kN',
                        'beton' : '',
                        'vedStreckenlast' : 'kN',
                        'p' : fracSmall('kN', 'm'),
                        'L' : 'm',
                        'vedEinzellast' : 'kN',
                        'bVed' : 'm',
                        'fed' : 'kN',
                        'vedAchse' : 'kN',
                        'vedRand' : 'kN',
                        'xAuflager' : 'm',
                        'vedStreckenlastVermindert' : 'kN',
                        'xVermin' : 'm',
                        'beta' : '',
                        'av' : 'mm',
                        'd' : 'mm',
                        'vedEinzellastVermindert' : 'kN',
                        'fed' : 'kN',
                        'vedVermindert' : 'kN',
                        'k': '',
                        'rho': '',
                        'zugbewehrung': 'mm²',
                        'breite': 'mm',
                        'fck' : fracSmall('N','mm²'),
                        'fcd' : fracSmall('N','mm²'),
                        'sigmaCp' : fracSmall('N','mm²'),
                        'ned' : 'kN',
                        'ac' : 'mm²',
                        'vRdcTmp' : 'kN',
                        'vMin' : fracSmall('N','mm²'),
                        'vMin600' : fracSmall('N','mm²'),
                        'vMin800' : fracSmall('N','mm²'),
                        'vRdc' : 'kN',
                        'cot0' : '',
                        'theta' : '°',
                        'vRdcc' : 'kN',
                        'zTmp' : 'cm',
                        'z' : 'mm',
                        'zGrenze' : 'mm',
                        'cv' : 'mm',
                        'sigmaCd' : fracSmall('N','mm²'),
                        'vRdMax' : 'kN',
                        'alpha' : '°',
                        'fywd' : fracSmall('N', 'mm²'),
                        'asw' : fracSmall('cm²', 'm'),
                        'aswMin' : fracSmall('cm²', 'm'),
                        'pWmin' : '‰',
                        'maxAbstand' : 'cm',
                        'delta' : fracSmall('cm²', 'm')
    }

    # Deklariert die Variablenbeschreibungen
    beschreibungen = {  'ved' : 'Die angegebene Querkraft',
                        'beton' : 'Der angegebene Beton',
                        'vedStreckenlast' : 'Die Querkraft infolge der gleichmäßigen Streckenlast',
                        'p' : 'Die gleichmäßige Streckenlast',
                        'L' : 'Die Länge des Balkens',
                        'vedEinzellast' : 'Die Querkraft infolge der Einzellast',
                        'bVed' : 'Der Abstand der Einzellast zur Auflagerachse des nicht nahen Auflagers',
                        'fed' : 'Die Einzellast',
                        'vedAchse' : 'Die Querkraft in der Auflagerachse',
                        'vedRand' : 'Die Querkraft am Auflagerrand',
                        'xAuflager' : 'Der Abstand von der Auflagerachse zum Auflagerrand',
                        'vedStreckenlastVermindert' : 'Die verminderte Querkraft infolge der gleichmäßigen Streckenlast',
                        'xVermin' : 'Der Abstand von der Auflagerachse bis statische Höhe d vom Auflagerrand',
                        'beta' : 'Der Abminderungsfaktor der Einzellast. '+BETHA+' = av / ( 2 * d)',
                        'av' : 'Der Abstand der Einzellast zum Auflagerrand',
                        'd' : 'Die Statische Höhe',
                        'vedEinzellastVermindert' : 'Die verminderte Querkraft infolge der Einzellast',
                        'fed' : 'Die angreifende Einzellast',
                        'vedVermindert' : 'Die gesamte verminderte Querkraft',
                        'k': 'Der Maßstabsfaktor',
                        'rho': 'Der Längsbewhrungsgrad',
                        'zugbewehrung': 'Die Fläche der Zugbewehrung',
                        'breite': 'Die Querschnittsbreite',
                        'fck' : 'Der charakteristische Wert der Betondruckfestigkeit',
                        'fcd' : 'Der Bemessungswert der Betondruckfestigkeit',
                        'sigmaCp' : 'Der Bemessungswert der Betonlängsspannung in Höhe des Schwerpunkts des Querschnitts',
                        'ned' : 'Die Bemessungswert der Normalkraft im Querschnitt infolge äußerer Einwirkungen ({} > 0 als Längsdruckkraft)'.format(namen['ned']),
                        'ac' : 'Die Querschnittsfläche des Betonbalkens',
                        'vRdcTmp' : 'Die aufnehmbare Querkraft ohne Querkraftbewehrung',
                        'vMin' : 'Die Spannung',
                        'vMin600' : 'Die Spannung für d ' + KLEINERGLEICH + ' 60cm',
                        'vMin800' : 'Die Spannung für d > 80 cm',
                        'vRdc' : 'Die aufnehmbare Querkraft ohne Querkraftbewehrung',
                        'cot0' : 'Der Cotangens der Druckstrebenneigung ' + THETA,
                        'theta' : 'Der Neigungswinkel der Druckstreben',
                        'vRdcc' : 'Die aufnehmbare Querkraft mit Bügelbewehrung',
                        'zTmp' : 'Der Hebelarm der inneren Kräfte (vereinfacht berechnet)',
                        'z' : 'Der Hebelarm der inneren Kräfte (vereinfacht berechnet)',
                        'zGrenze' : 'Die obere Grenze für z',
                        'cv' : 'Die Betondeckung der Längsbewehrung ' + sub('c', 'vl'),
                        'sigmaCd' : 'Der Bemessungswert der Betonlängsspannung in Höhe des Schwerpunkts des Querschnitts (ohne obere Grenze)',
                        'vRdMax' : 'Der Bemessungswert der Betondruckstreben (bei Bauteilen mit Querkraftbewehrung)',
                        'alpha' : 'Der Winkel in welchem die Querkraftbewehrung angeordnet ist',
                        'fywd' : 'Der Bemessungswert der Betonstahlstreckgrenze',
                        'asw' : 'Die rechnerisch erforderliche Querkraftbewehrung',
                        'aswMin' : 'Die mindestquerkraftbewehrung',
                        'pWmin' : 'Der Mindestbewehrungsgrad (auch Mindestschubbewehrungsgrad genannt)',
                        'maxAbstand' : 'Der maximale Abstand der Bügel',
                        'delta' : 'Die gewählte Querkraftbewehrung'
    }


    # Alle Eingabeparameter am System
    eingabeparameterSystem = {  'hohe'           : fixLength('Höhe', 18) + '= {} cm',
                                'breite'         : fixLength('Breite', 18) + '= {} cm',
                                'lange'          : fixLength('Länge', 18) + '= {} m',
                                'last'           : fixLength('Last', 18) + '= {} kN/m',
                                'statHohe'       : fixLength('statische Höhe', 18) + '= {} cm',
                                'auflagertiefe'  : fixLength('Auflagertiefe', 18) + '= {} cm',
                                'zugbewehrung'   : fixLength('Zugbewehrung', 18) + '= {} cm²',
                                'cv'             : fixLength('Verlegemaß', 18) + '= {} cm',
                                'alpha'          : fixLength('Alpha', 18) + '= {} °',
                                'ned'            : fixLength(sub('N', 'Ed'), 18) + '= {} kN',
                                'fed'            : fixLength(sub('F', 'Ed'), 18) + '= {} kN',
                                'av'             : fixLength('Abstand Einzellast', 18) + '= {} cm',
                              }

    # Alle Eingabeparameter am Schnitt
    eingabeparameterSchnitt = { 'hohe'           : fixLength('Höhe', 18) + '= {} cm',
                                'breite'         : fixLength('Breite', 18) + '= {} cm',
                                'statHohe'       : fixLength('statische Höhe', 18) + '= {} cm',
                                'zugbewehrung'   : fixLength('Zugbewehrung', 18) + '= {} cm²',
                                'cv'             : fixLength('Verlegemaß', 18) + '= {} cm',
                                'alpha'          : fixLength('Alpha', 18) + '= {} °',
                                'ned'            : fixLength(sub('N', 'Ed'), 18) + '= {} kN',
                                'qed'            : fixLength(sub('V', 'Ed, vermindert'), 18) + '= {} kN',
                                'qed_rand'            : fixLength(sub('V', 'Ed, Rand'), 18) + '= {} kN',
                              }
    
    # spezifische Ausgabeparameter am System
    ausgabeparameterSystem = ['vedAchse', 'vedRand', 'vedVermindert'] # 'd', 'k', 'rho', 'zugbewehrung', 'vRdc', 'vRdcc', 'cot0', 'z', 'sigmaCd', 'sigmaCp', 'vRdMax', 'asw', 'aswMin', 'pWmin']

    # spezifische Ausgabeparameter am Schnitt
    ausgabeparameterSchnitt = ['ved'] # 'd', 'k', 'rho', 'zugbewehrung', 'vRdc', 'vRdcc', 'cot0', 'z', 'sigmaCd', 'sigmaCp', 'vRdMax', 'asw', 'aswMin', 'pWmin']

    # alle anderen Ausgabeparameter
    ausgabeparameter = {'d'             : 'mm',
                        'k'             : '',
                        'rho'           : '',
                        'zugbewehrung'  : 'cm²',
                        'vRdc'          : 'kN',
                        'vRdcc'         : 'kN',
                        'cot0'          : '({}°)'.format(round(zwischenwerte['theta'], RUNDUNG)),
                        'z'             : 'mm',
                        'sigmaCd'       : 'N/mm²',
                        'sigmaCp'       : 'N/mm²',
                        'vRdMax'        : 'kN',
                        'asw'           : 'cm²',
                        'aswMin'        : 'cm²',
                        'pWmin'         : ''
                        }

