# USDZerveApp - Convert an USDA text file made by a WebApp to a servable USDZ archive

It needs Python 2.7 installed on your IIS-Server machine and CGI activated. 
With a few patches (focussing on `print`) it might as well run on Python 3.x, but since other USD related python tools don't support 3.x yet, I stayed on 2.x.

It also needs Pixar @openUSD installed.
A well prepared fork including binary releases can be found at: [VictorYudin/saturn](https://github.com/VictorYudin/saturn)

Use **IIS-Server-Manager** GUI to add the following:

* Add a new **MIME-Type** (preferrably to the whole domain): 
  `.usdz model/vnd.usdz+zip`
  This allows the server to allow downloads of 3D product presentations properly.
  
* Add an **Application** of type **Script**:
  `usdzerve` pointing to `C:\usdzerve\`  
  Copy `createbasket.py` to this folder.


* Add a new **handler**:
  `.py` calling `C:\Python27\python.exe %s %s C:\inetpub\wwwroot\models`
  
* **Add rights** to several folders `C:\inetpub\wwwroot\models`, `C:\usdzerve\` to allow the process to **write and execute**:
  ```
  icacls . /grant "NT AUTHORITY\IUSR:(OI)(CI)(RX)"
  icacls . /grant "Builtin\IIS_IUSRS:(OI)(CI)(RX)"
  ```

Instead of using the recommended `usd.cmd` shell script to start USD related scripts interactively, 
we have to properly set a couple of System environment variables to point to both the DLLs, 
Libraries and Scripts extending Python for @openUSD.

```
set USD_INSTALL_ROOT=C:\USD
set PATH=%USD_INSTALL_ROOT%;%USD_INSTALL_ROOT%\bin;%USD_INSTALL_ROOT%\lib\usd;%PATH%
set PYTHONPATH=%USD_INSTALL_ROOT%\lib\python;%PYTHONPATH%
```
