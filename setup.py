import PyInstaller.__main__
import platform
import os
    
scriptDir = os.path.dirname(os.path.realpath(__file__))
if platform.system() == "Windows":
     PyInstaller.__main__.run([  
          '-n%s' % 'Balken',
          '--onefile',
          '--windowed',
          '--icon=%s'     % 'res\icon.ico',
          '--add-data=%s' % 'res\start.ui;res',
          '--add-data=%s' % 'res\system.ui;res',
          '--add-data=%s' % 'res\schnitt.ui;res',
          '--add-data=%s' % 'res\iconFragezeichen.png;res',
          '--add-data=%s' % 'res\icon.png;res',
          '--add-data=%s' % 'res\schnitt.png;res',
          '--add-data=%s' % 'res\system.png;res',
          '--add-data=%s' % 'res\wkhtmltopdf.exe;res',
          '--add-data=%s' % 'res\\template.html;res',
          '--add-data=%s' % 'res\output.html;res',
          '--add-data=%s' % 'res\\README.txt;res',
          '--clean',
          os.path.join(scriptDir, 'querkraft.py'),                                         
     ])

else:
     PyInstaller.__main__.run([  
         '-n%s' % 'Balken',
          '--onefile',
          '--windowed',
          '--icon=%s'     % 'res/icon.ico',
          '--add-data=%s' % 'res/start.ui:res',
          '--add-data=%s' % 'res/system.ui:res',
          '--add-data=%s' % 'res/schnitt.ui:res',
          '--add-data=%s' % 'res/iconFragezeichen.png:res',
          '--add-data=%s' % 'res/icon.png:res',
          '--add-data=%s' % 'res/schnitt.png:res',
          '--add-data=%s' % 'res/system.png:res',
          '--add-data=%s' % 'res/template.html:res',
          '--add-data=%s' % 'res/output.html:res',
          '--add-data=%s' % 'res/README.txt:res',
          '--clean',
          os.path.join(scriptDir, 'querkraft.py'),                                         
     ])