# usdzerve - Build USDZ archive representing a webshop cart

This is the most simple application, as it only needs a set of existing product USDZ files to combine to a so called asset library, supported by AR Quicklook from iOS13 on.

It needs Python 2.7 installed on your IIS-Server machine and CGI activated. 
With a few patches (focussing on `print`) it might as well run on Python 3.x, but since other USD related python tools don't support 3.x yet, I stayed on 2.x.

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

This python script is based on **usdzcreateasstlib** provided by Apple in its WWDC 2019 **USD Tools** collection.

The changes I made are:

* Make commandline parameters match the way IIS calls python scripts.

* Allow more than one instance of a product/item to be included to a cart USDZ.
