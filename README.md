# DataRecorder

## Definitionen
- **Rohdaten**: So, wie ein Signal am Sensoreingang empfangen wird (**mA** oder **V**).
- **Messdaten**: Daten mit physikalischen Einheiten (z.B. **°C**)

## Einleitung
Das Ziel dieses Projekts ist es einen Messdaten-Recorder mit einer Strommessung im 4-20 **mA** Bereich zu entwickeln. Die Rohdatenerfassung soll nach der Projektspezifikation über 24 **h** lang mit einem (konfigurierbaren) Erfassungsintervall von 1 **s** bis mehreren **min** erfolgen. Als Erfassungshardware wird der Yocto-4-20mA-Rx [9] von der Schweizer Firma Yoctopuc [8] verwendet. Die Rohdaten werden über eine konfigurierbare lineare Funktion in physikalische Messwerte umgerechnet. Die Messwerte sollen neben der Darstellung im grafischen User Interface (GUI) auch auf der Harddisk als CSV File als physikalische Messwerte abgespeichert werden. Im GUI werden die Messwerte (aktuelle, sowie die minimalen als auch die maximalen Messwerte) graphisch dargestellt.

Im einem zweiten Schritt soll die Applikation mit einer Emulator Funktion erweitert werden. Der Emulator (Yoctopuc[8] Emulator Modul [10]) soll dann in der Lage sein, die vom Rekorder aufgezeichneten Temperaturverläufe in Stromwerte umzuwandeln und über eine einstellbare Stromquelle abzuspielen. Als Ziel ist es mit bis 12 Emulatoren bis zu 12 Rekorder Kanäle falsche Messwerte abzuspielen (Emulator Teil gehört nicht zur Arbeitsprobe).

Das Programm soll eine konfigurierbare Anzahl Messsensoren als Empfänger unterstützen und später - bei der Realisierung des Emulators - die Transmittermodule. Als Konfigurationsdatei wird ein XML Format verwendet, in dem die zu verwendenden Sensoren und Transmitter persistent abgespeichert werden. Die verwendete Umwandlungsformel ist in der Konfigurationsdatei festgelegt. Die im GUI eingestellte Messdauer und die Erfassungsperiode soll sofort in der Konfigurationsdatei abgespeichert werden, so dass beim nächsten Start der Applikation die letzten Einstellungen konfiguriert werden.

## Architektur 

### Übersicht
Eingangspunkt für die Anwendung ist das Graphische User Interface (GUI), implementiert in der Klasse *SensorDisplay* (in 'DataRecorder.py'). Die Datenerfassung ist in der Klasse *YoctopuceTask* ('YocotopucTask.py') gekapselt und zur Speicherung der persistenten Konfiguration wird eine *configuration* Klasse in 'configuration.py' verwendet. 

Das Graphische User Interface (GUI) besteht aus zwei Tabs (Rekorder und Emulator) und einer Menu Bar. In der Menu Bar kann man - nach dem Vollausbau der Anwendung - über einen Dateibrowser Emulator Daten laden, die im Emulator Tab graphisch dargestellt werden. 

### Graphisches User Interface (GUI)
Das Recorder Tab zeigt die Hauptfunktionalität der Anwendung. Es zeigt als Graphik den Verlauf der Messwerte mit den Legenden aller Sensoren. Als Zeitachse (X-Achse) dient die Zeit seit dem Start der Aufzeichnung, in der Y-Achse ist die physikalische Einheit aufgeführt. Die darzustellenden Sensorgraphen pro Sensor können separat ein- und ausgeschaltet werden. Pro Achse kann eine fixe oder eine variable Skalierung vorgegeben werden. Wenn variabel gewählt wird, können die Darstellungsbereiche (min, max) nummerisch eingegeben werden. Das Sampleintervall kann mit einem integer Wert und einer Einheit in **ms**, **s** oder **min** konfiguriert werden. In der gleichen Art kann die Erfassungszeit in ,**s**, **min** und **h** eingestellt werden. 

Weiter sind auf dem Rekorder Tab des *SensorDisplay* die Bedienelemente, um die Aufzeichnung zu steuern. Ist ein Sensor eingesteckt kann mit einem `Start`-Knopf die Aufzeichnung gestartet werden. Beim `Start` der Applikation wird die Konfiguration geladen. Diese Funktionalität ist in 'configuration.py' implementiert. Die damit verbundene Klasse *configuration* liest die Konfigurationsdatei ('configuration.xml') ein und ermittelt daraus die lineare Funktion, mit der pro angeschlossenen Sensor die Rohwerte (**mA**) in physikalische Einheiten (z.B. **°C**) umgerechnet werden können. Diese Funktionen werden von der Klasse *configuration*  als Closure zur Verfügung gestellt. *configuration* wird in  der Klasse *SensorDisplay* instanziiert und diese Closure werden vom Datenrekorder für die Umrechnung der Rohwerte in physikalische Einheiten verwendet. Nachfolgend ist ein Ausschnitt dieser Konfigurationsdatei 'configuration.xml' dargestellt:

![Xml Konfiguration](./xmlConfig.png)

Als Datenquelle erhält das *SensorDisplay* Signale von der Erfassungsklasse *YoctopuceTask* (siehe nächster Abschnitt) mit Rohdaten in **mA** von der Datenerfassung, deren Wert eine gültige float Zahl ist, oder - im Fall wenn kein Sensor vorhanden ist - `np.NaN`. 

Bei laufender Aufzeichnung werden die erfassten Werte fortlaufend im Graph des Recorder Tabs dargestellt.  Wird während der Aufzeichnung der Sensor ausgesteckt, werden von der Erfassungsklasse `np.NaN` geliefert was zu Lücken) im Graph führt, steckt der Nutzer den Sensor wieder ein, wird die Aufzeichnung und Darstellung der Daten wieder fortgesetzt. 

Mit dem Drücken des `Start` Knopfs, wird die Aufzeichnung gestartet. Jetzt kann über einen `Stop`-Knopf - nach einer bestätigenden Nachfrage - die Erfassung beendet werden. Dadurch hat der Nutzer nun die Möglichkeit, die Aufzeichnung mit einem `Clear`-Knopf - nach einer bestätigenden Nachfrage - zu löschen oder mittels eines `Save`-Knopfes als CSV Datei abzuspeichern. Will der Nutzer die Daten abspeichern geht ein Dateidialog auf, in dem der Nutzer einen Speicherort und einen Dateinamen eingeben kann. In der ersten Spalte dieser Datei ist der nach Spezifikation geforderte ISO Zeitstempel aufgeführt. Dann folgt die relative Zeit in Sekunden seit Messbeginn und die Messwerte und Einheiten (**°C**, **mA**) aller Sensoren. Im Header der Datei sind die verwendeten Sensoren aufgeführt und die physikalischen Einheitn der abgespeicherten Messgrössen. Bei einer laufenden Aufzeichnung wird mit dem Zeitstempel des Startzeitpunkts (z.B. 20230403_102958.csv) eine Datei im oben erwähnten Datenformat erzeugt, in der die erfassten Daten abgespeichert werden. Wird der Sensor ausgesteckt, wird zu diesem Zeitpunkt eine NaN Datei (z.B. 20230403_103008_NaA.csv) erstellt und die Daten in diesem Zustand darin abgespeichert. 

Während der Aufzeichnung wird der aktuelle Messwert, der minimale und maximale Messwert in einem Bereich des GUI Nummerisch ausgegeben. Diese Informationen sind ebenfalls in einem anderen Teil des GUIs für die Rohwerte ersichtlich. 

Am Ende des Konstruktors der Applikation *SensorDisplay* wird als nebenläufiger Task die *YoctopuceTask* Klasse instanziiert.  Dies ermöglicht die Konfiguration der Datenerfassung (nächster Abschnitt) vom Datenrekorder aus. Nach dem Erstellen des GUIs wird in der Applikation durch den Start des QT-Eventloop gestartet. Im Folgenden geben die Events im System die Funktionalität vor. 

### Datenerfassung
*YoctopuceTask* ist die low level Basis der Applikation und befindet sich in 'YoctopucTask.py'. Sie dient als Schnittstelle zum API des Herstellers ('yocto_api' und 'yocto_genericsensor'). *YoctopuceTask* stellt die Funktionalität zur Verfügung um die high level Anforderungen des *SensorDisplay*/Datenrekorder in 'yocto_api' Aufrufe umsetzt. So kann der Datenrekorder dem 'YoctopucTask' mitteilen, mit welchem Sampleintervall (**ms**, **s**, **min**) er wie wie viele Samples er erfassen soll. Mit diesen Angaben konfiguriert er über die Herstellerklasse die zwei Yoctopuc Sensoren, die in unserem Fall Strom im Bereich von 4-20 *mA* detektieren können. Ebenfalls wird hier mit einem `superVisorTimer` garantiert - auch bei ausgesteckten Sensoren - Daten liefert. 

In der Yoctopuc Bibliotheke wird die Methode 'new_data' in *YoctopuceTask* als call back registriert, der von Yoctopuc regelmässig mit aktuellen Rohwerten aufgerufen wird. Beim erstmaligen Aufrufen dieser Funktion wird ein Überwachungstimer (`superVisorTimer`) mit der Methode 'FakeCB' als call back und dem Sampleintervall aufgesetzt. Das Ausstecken eines Sensors setzt in 'deviceRemoval' (registriert als call back in der Herstellerklasse) ein Attribut ('connected') der Instanz auf `False`. Wenn in der regelmässigen Überwachungsfunktion 'fakeCB' das Attribut 'connected' deaktiviert ist, übernimmt 'fakeCB' als regelmässiger Datenlieferant. Um dem *SensorDisplay* mitzuteilen, dass momentan keine Daten erhältlich sind wird - wie wenn kein Strom gemessen wird - der Wert `np.nan` weitergeleitet. Wenn der Sensor wieder eingesteckt wird, wird 'connected' wieder auf True gesetzt, 'fakeCB' deaktiviert und Yoctopuc liefert dem Rekorder wieder Daten. Die regelmässigen Rohwerte in (**mA** oder die nicht konnektierten `np.nan` Werte)  werden als Signal an das *SensorDisplay* geschickt.


### Spielfeld
Als Spielfeld zum Kennenlernen der Sensoren und der Herstellerbibliotheke wurde ein Stand Alone script `producer.py` implementiert. Damit kann hardcodiert in einer definierten Datenrate eine bestimmte Anzahl (während 24h erfolgt jede Minute eine Messung, das entspricht total 1440 Messwerte) Messwerte erfasst werden und in ein CSV File gespeichert werden.

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
12.  M. Summerfield, Rapid GUI Programming with Python and Qt: The Definitive Guide to PyQt Programming, 1. Aufl. Pearson, 2007.

Source library can be downloaded from <https://www.yoctopuce.com/FR/downloads/YoctoLib.python.52382.zip> and unziped in a folder above this folder and rename it to yoctolib_python.