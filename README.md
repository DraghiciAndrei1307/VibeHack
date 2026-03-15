# VibeHack

## Description

This is the solution that the 'Two Devs One Repo' team developed during a 2-day VibeHack hackathon. It was a nice 
challenge from which we had a lot of things to learn. 

## How to use

1) The first thing you have to do is to clone this repo, using the following command:

```commandline
git clone https://github.com/DraghiciAndrei1307/VibeHack.git
```
2) The second thing you have to do is to create yourself a virtual environment (you need to have Python 3 installed on 
your machine), using the following commands to create and load it:

```commandline
python3 -m venv .venv

source .venv/bin/activate
```

3) Before you run this project, you will have to install all the requirements contained by the requirements.txt:

```commandline
pip install -r requirements.txt
```

4) After you installed all prerequisites, you need to create the environment variables (the SID, TOKEN and API_KEY). 
Make sure you add them at the end of the ~/.venv/bin/activate file and then you reload the environment.

```commandline
export API_KEY=<your_featherless_ai_key>_
export SID=<your_Twillio_sid>
export TOKEN=<your_Twillio_token>

source .venv/bin/active
```

5) Another important thing that we used was the ngrok which is ' all-in-one cloud networking platform that secures, 
transforms, and routes your traffic to services running anywhere'. 

To use ngrok, you need to create an account here: https://ngrok.com/ 

After you created an account there, you need to add your private authtoken:

```commandline
ngrok config add-authtoken <your_private_ngrok_token>
```

Next, you have to run the ngrok on you local host (on a designated opened port that you are working on):

```commandline
ngrok http 9000
```

```terminaloutput
ngrok                                                                                                                          (Ctrl+C to quit)
                                                                                                                                               
🚪 One gateway for every AI model. Available in early access now: https://ngrok.com/r/ai                                                     
                                                                                                                                               
Session Status                online                                                                                                           
Account                       draghiciandrei122@gmail.com (Plan: Free)                                                                         
Version                       3.37.2                                                                                                           
Region                        Europe (eu)                                                                                                      
Latency                       58ms                                                                                                             
Web Interface                 http://127.0.0.1:4040                                                                                            
Forwarding                    https://unhastily-leafed-nell.ngrok-free.dev -> http://localhost:5001                                            
                                                                                                                                               
Connections                   ttl     opn     rt1     rt5     p50     p90                                                                      
                              3       0       0.00    0.00    0.02    0.02                                                                     
                                                                                                                                               
HTTP Requests                                                                                                                                  
-------------
```

Basically, all traffic that the ngrok endpoint `https://unhastily-leafed-nell.ngrok-free.dev` receives is redirected to 
the localhost endpoint `localhost` through port 5001. 
 
## What makes this project special? 





