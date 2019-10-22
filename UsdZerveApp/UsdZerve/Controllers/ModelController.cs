using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Web.Http;
using System.Diagnostics;
using System.IO;

namespace USDZerve.Controllers
{
    public class ModelController : ApiController
    {
        const string key = "SecretKey"; // \todo change!
        const string modelPath = "C:\\inetpub\\wwwroot\\models\\";
        // POST: api/Model?uuid=xxxxx Takes the UUID from Uri and the HTTP[s] body is the .usda content to be saved to disk
        public string Post([FromUri]string uuid, [FromUri]string productKey, [FromUri]string procedure)
        {
            if (productKey == key)
            {
                if (procedure == "usda2z")
                {
                    // take text for USDA file from request and save it locally
                    System.IO.File.WriteAllText(modelPath + uuid + ".usda", this.Request.Content.ReadAsStringAsync().Result);
                    try
                    {
                        Process p1 = new Process();
                        p1.StartInfo.WorkingDirectory = modelPath;
                        p1.StartInfo.CreateNoWindow = true;
                        p1.StartInfo.UseShellExecute = false;
                        p1.StartInfo.FileName = "C:\\Python27\\python.exe";
                        p1.StartInfo.Arguments = "C:\\usdzerve\\usdcat.py -o " + uuid+".usdc "+uuid+".usda";
                        p1.Start();
                        p1.WaitForExit();

                        Process p2 = new Process();
                        p2.StartInfo.WorkingDirectory = modelPath;
                        p2.StartInfo.CreateNoWindow = true;
                        p2.StartInfo.UseShellExecute = false;
                        p2.StartInfo.FileName = "C:\\Python27\\python.exe";
                        p2.StartInfo.Arguments = "C:\\usdzerve\\usdzip.py --checkCompliance " + uuid + ".usdz " + uuid + ".usdc";
                        p2.Start();
                        p2.WaitForExit();

                        System.IO.File.Delete(modelPath + uuid + ".usda");
                        System.IO.File.Delete(modelPath + uuid + ".usdc");
                        return "models/" + uuid + ".usdz";
                    }
                    catch (UnauthorizedAccessException e)
                    {
                        System.IO.File.Delete(modelPath + uuid + ".usda");
                        return "ERROR: " + e.Message;
                    }
                }
                else if (procedure == "usdatex2z") // this will also include all textures in subfolder \0\
                {
                    // take text for USDA file from request and save it locally
                    System.IO.File.WriteAllText(modelPath + uuid + ".usda", this.Request.Content.ReadAsStringAsync().Result);
                    try
                    {
                        Process p1 = new Process();
                        p1.StartInfo.WorkingDirectory = modelPath;
                        p1.StartInfo.CreateNoWindow = false;
                        p1.StartInfo.UseShellExecute = false;
                        p1.StartInfo.FileName = "C:\\Python27\\python.exe";
                        p1.StartInfo.Arguments = "C:\\usdzerve\\usdcat.py -o " + uuid + ".usdc " + uuid + ".usda";
                        //p1.StartInfo.RedirectStandardError = true;
                        p1.Start();
                        p1.WaitForExit();

                        string textures = "0/kiefer_4096.jpg";
                        Process p2 = new Process();
                        p2.StartInfo.WorkingDirectory = modelPath;
                        p2.StartInfo.CreateNoWindow = false;
                        p2.StartInfo.UseShellExecute = false;
                        p2.StartInfo.FileName = "C:\\Python27\\python.exe";
                        p2.StartInfo.Arguments = "C:\\usdzerve\\usdzip.py --checkCompliance " + uuid + ".usdz " + uuid + ".usdc "+textures;
                        p2.Start();
                        p2.WaitForExit();

                        System.IO.File.Delete(modelPath + uuid + ".usda");
                        System.IO.File.Delete(modelPath + uuid + ".usdc");
                        return "models/" + uuid + ".usdz";
                    }
                    catch (UnauthorizedAccessException e)
                    {
                        System.IO.File.Delete(modelPath + uuid + ".usda");
                        return "ERROR: " + e.Message;
                    }
                }
                else
                {
                    return "ERROR: UnregisteredProcedure";
                }
            }
            else
            {
                return "ERROR: UnregisteredProductKey";
            }
        } 
    }
}
