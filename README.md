# DataRecorder

## Definitionen
- **Rohdate**: So, wie ein Signal am Sensor Eingang empfangen wird (**mA** oder **V**).
- **Messdate**: Daten mit physikalischen Einheiten (z.B. **°C**)

## Einleitung
Das Ziel dieses Projekts ist es einen Messdaten-Recorder mit einer Strommessung im 4-20 **mA** Bereich zu entwickeln. Die Rohdatenerfassung soll nach der Projektspezifikation über 24 **h** lang mit einem (konfigurierbarem) Erfassungsintervall von 1 **s** bis mehreren **min** erfolgen. Als Erfassungshardware wird der Yocto-4-20mA-Rx [9] von der Schweizer Firma Yoctopuc [8] verwendet. Die Rohdaten werden über eine konfigurierbare lineare Funktion in physikalische Messwerte umgerechnet. Die Messwerte sollen neben der Darstellung im grafischen User Interface (GUI) auch auf der Harddisk als CSV File abgespeichert werden. Im GUI werden die Messwerte (und Min/Max/Einheit) graphisch dargestellt.

Im zweiten Schritt soll im Anschluss an die Arbeitsprobe das Projekt so erweitert werden, dass aufgezeichnete Messwertdaten die als CSV Datei gelesen werden und über ein Yoctopuc[8] Emulator Modul [10] mit einem Strombereich von 4-20 **mA** ausgegeben werden. Der Verlauf der physikalischen Ausgabewerte soll im selben GUI, auf einem anderen Tab dargestellt werden.

Das Programm soll eine konfigurierbare Anzahl Messsensoren als Empfänger unterstützen und später - bei der 
Realisierung des Emulators - die Transmittermodule. Als Konfigurationsdatei wird ein XML Format verwendet, in dem 
die zu verwendenden Sensoren und Transmitter persistent abgespeichert werden. Die zu verwendete Umwandelformel ist 
in der Konfigurationsdatei festgelegt. Die im GUI eingestellten Messdaür und die Erfassungsperiode soll sofort in der Konfigurationsdatei abgespeichert werden, so dass beim nächsten Start der Applikation die letzten Einstellungen konfiguriert sind.

## Architektur (grob skizziert, noch zu verbessern)
Als Basis der Applikation dient die Klasse *YoctopuceTask* (in File 'YoctopucTask.py') welche die low-level Anbindung an die Herstellerbibliotheke 

Das 'DataRecorder.py' ist der Eintrittspunkt zum Programm. Es erstellt das GUI in der *SensorDisplay* Klasse das aus zwei Tab (Rekorder und Emulator) besteht. Am Ende des GUI Konstruktors wir in einem nebenläufiger Prozess die  instanziert. 

In dieser Klasse werden die vom Hersteller bereitgestellten APIs ('yocto_api' und 'yocto_genericsensor') eingebunden. Diese Klasse stellt die Funktionalitaet zur Verfügung um die high level Anforderungen des Datenrekorders in 'yocto_api' aufrufe umsetzt. So kann der Datenrekorder der 'YoctopucTask' mitteilen, mit welchem Sampleintervall (**s**, **ms**) er wie lange (in **d**, **h**, **m** oder **s**) er erfassen soll. *YoctopuceTask* liefert die erfassten Rohwerte als Signale an den Datenrekorder. Im 'YoctopucTask' kapselt eine 'sensor' Klasse die Yoctopuc Sensoren. Ebenfalls sinalisiert diese Klasse dem Datenrekorder, das Sensoren eingesteckt oder ausgesteckt worden sind. Laeuft eine Aufzeichung und der Sensor wird ausgesteckt werden im "NaN" Erfassungswert an den Rekorder geliefert, der dies erkennen muss und entsprechende Vorkehrungen bei der Darstellung der graphischen Werte treffen muss.      

Ist der *YoctopucTask* aufgesetzt, kann der Datenrekorder eine Aufzeichnung über eine 'Start' Knopf im Recoder Tab starten. Die erfassten Werte werden fortlaufend im Graph des Recordertabs dargestellt. Läuft die Aufzeichnung, kann über einen 'Stop' Knopf beendet werden. Dadurch hat der Nutzer nun die Möglichkeit, die Daten zu mit einem 'Clear' Knopf zu löschen oder in mittels eines 'Save' Knopf abzuspeichern. Will der Nutzer die Daten abspeichern geht ein Dateidialog auf, in dem der Nutzer einen Speicherort und einen Dateinamen angeben kann. Wird während der Aufzeichnung der Sensor ausgestreckt, werden keine weiteren Daten dargestellt (Lücken), steckt der Nutzer den Sensor wieder ein, wird die Aufzeichnung und Darstellung wieder fortgesetzt. 


Über eine Konfigurationsklasse 'configuration' in der Datei 'configuration.py' wird mithilfe des XML Konfigurationsdatei 'configuration.xml' die über USB angebunden Sensoren konfiguriert. Die ID der Sensoren gibt den Sensortyp vor. Im der Konfigurationsdatei steht für jeden Sensor ID im System eine lineare Umrechnungsformel, welche die Rohwerte (**mA**, **V**) in Messwert ('**°C**') umrechnet. Die Konfigurationsdatei stellt Funktionen als Closure zur Verfügung mit welcher der Datenrecorder die Rohwerte in physikalische Werte umgerechnet werden koennen. 



Mit dem Start des Yoctopuc APIs kann der Datenrecorder eine Aufzeichnug starten. Das System ist so aufgesetzt, dass fortlaufend Daten erfasst werden, auch wenn der USB Sensor ausgesteckt wird. Werden die Sensoren detektiert, sie in eine *sensor* Klasse eingepackt und als Dictionary (Key ist die Sensorfunktion) in der Yoctopuc Klasse abgespeichert. Ferner weden als statische Variablen Signale aufgesetzt, die als Kommunikationsmittel zwischen dem GUI und Low-level Sensoranbindung fungieren.

Wenn ein Sensor eingesteckt werden erscheint auf dem Recoder Tab einen `Start` Knopf. Nach dem Einstellen der Erfaaungszeit und des Sampleintervalls wir die Erfassung gestartet. Dadurch wir der `Start` Knopf nicht mehr dargestellt, und es erscheint einen `Stop` Knopf. Mit dem drücken diese Knopfs wird nachgefragt ob man wirklich beenden will. Wird dies bestätigt Erscheine die Knöpfe `Clear` und `Save`. Mit Clear wird die Messung gelöscht und man kommt in den Ursprungszustand der Anwendung (nur `Start` Knopf sichtbar). Ueber den `Save` Knopf wir ein Filedialog dargestellt mit dem man einen Namen für eine Datei eingegeben kann unter der die erfassten Daten Spaltenweise abgelegt. In der ersten Spalte ist der der erforderte ISO Zeitstempel des Messmoment, in der zweiten Spalte ist die Relative Zeit in `s` seit Messbeginn aufgeführt. In den weiteren Spalten ist für jeden angeschlossenen Sensor der Messwert un die Messgrösse augeführt.

Ein Problem stellt dar, wenn die Sensoren ausgesteckt währenden die Aufzeichnung läuft. In der Funktion `new_data` in der von der Yoctopuc Bibotheke die neuen Messwerte mitgeteilt werden muss überwacht werden, dass auch regelmässig Daten empfangen werden. Daher wird beim erstmaligen Aufruf dieser Funktion ein einen repetitiven Counter mit der Callbackfunktion  `self.superVisorTimer` und einer etwas grösseren Periode als die Sample periode (`self.sampel_interval_ms`) aufgesetzt. In diese Funktion wir auch eine Membervariable (`self.onGoing`) auf True gesetzt. Als Callback Funktion wird  die `self.new_data_superVisor` Methode aufgesetzt. Im erstmaligen Aufruf wir das Aufrufintervall auf das Sample Intervall abzüglich einen kleines Offse gesetzt das `self.onGoing` Flag auf False gesetzt und als Callback eine Funktion  (fakeCB) aufgesetzt die falsche Daten `new_data` übergibt. Weiter wird inn `self.new_data_superVisor` da das `self.onGoing` flag auf False gesetz. 


Als Spielfeld zum Kennenlernen der Sensoren und der Herstellerbibliotheke wurde ein Stand Alone script `producer.py` das hardcodiert in einer definierten Datenrate ein bestimmte Anzahl (24x60= 1440 = 1 Messpunkt pro Minute) Messwerte erfasst und in ein CSV File gespeichert.

![Model View Controller Aufbau](./mvc.png)

## Graphic User Interface (GUI)
Das Graphic User Interface (GUI) ist in der Datei `gui.py` implementiert. Als Bibliotheke wird PyQt [11] verwendet. Diese Biblioteke stellt die Funktionalität zur Verfügung um ein graphisches Fenster plattformunabnhänig zu implementieren. Das hat `DataRecorder` steht in der Titelbar. Es folgt eine Menubar mit den Einträgen `File` und `About` .

Im folgenden werden als Tabs sowohl ein Recorder als auch eine Emulatorgrafik (Optional) dargestellt. Im Erfassungstab wird die aktuelle Erfassungszeit und die aktuelle Erfassungsrate dargestellt. Wird dieser Wert geändert, wird daraus wieder ein `configuration.xml` erstellt und abgespeichert. In einer Legende können die erfassenden Sensoren selektiert werden, die dann in °C in der Grafik des Tabs dargestellt werden.  Die Grafik ist in einem Sliding Fenster dargestellt um den interessierten Bereich der Daten darzustellen.

## Konfiguration
![Xml Konfiguration](./xmlConfig.png)

## Referenzen
1. „GitHub Flavored Markdown Spec“. https://github.github.com/gfm/#example-14 (zugegriffen 15. Januar 2023).
2. J. M. Willman, Beginning PyQt: A Hands-on Approach to GUI Programming with PyQt6, 2nd ed. Apress, 2022.
3. B. Okken, „Python Testing with Pytest: Simple, Rapid, Effective, and Scalable: Simple, Rapid, Effective, and Scalable : Okken, Brian: Amazon.de: Bücher“, 2022.
4. E. Gamma, R. Helm, R. E. Johnson, und J. Vlissides, Design Patterns. Elements of Reusable Object-Oriented Software., 1st ed., Reprint Edition. Reading, Mass: Prentice Hall, 1997.
5. M. Fitzpatrick, „Create GUI Applications with Python & Qt5 (5th Edition, PyQt5): The hands-on guide to making apps with Python : Fitzpatrick, Dr Martin.
6. D. Beazley, Python Essential Reference, 4. Aufl. Upper Saddle River, NJ: Addison-Wesley Professional, 2009.
7. D. Bader, Python-Tricks: Praktische Tipps für Fortgeschrittene, 1. Aufl. Heidelberg: dpunkt.verlag GmbH, 2018.
8. [yoctopuc](https://www.yoctopuce.com/)
9. [Yocto-4-20mA-Rx](https://www.yoctopuce.com/EN/products/usb-electrical-interfaces/yocto-4-20ma-rx)
10. [Yocto-4-20mA-Tx](https://www.yoctopuce.com/EN/products/usb-electrical-interfaces/yocto-4-20ma-tx)
11. [PyQt](https://www.qt.io/)
12. [1] M. Summerfield, Rapid GUI Programming with Python and Qt: The Definitive Guide to PyQt Programming, 1. Aufl. Pearson, 2007.

Source library can be downloaded  from <https://www.yoctopuce.com/FR/downloads/YoctoLib.python.52382.zip> and unzip in a folder above this folder and rename it to yoctolib_python.
