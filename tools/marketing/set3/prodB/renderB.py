import asyncio,sys,subprocess,os,time
from playwright.async_api import async_playwright
async def render(html,out,dur,fps=30,audio=None,start=0,end=None):
    async with async_playwright() as pw:
        b=await pw.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--allow-file-access-from-files','--disable-web-security'])
        p=await (await b.new_context(viewport={'width':1080,'height':1920},device_scale_factor=1)).new_page()
        p.on('pageerror',lambda e:print('ERR',e));p.on('console',lambda m:print('LOG',m.text) if m.type=='error' else None)
        await p.goto('file://'+html);await p.evaluate("()=>window.__ready");await p.wait_for_timeout(400)
        n=int(round(dur*fps));tmp=out[:-4]+'.part.mp4'
        cmd=['ffmpeg','-y','-v','error','-f','image2pipe','-framerate',str(fps),'-c:v','mjpeg','-i','-']
        if audio:cmd+=['-i',audio,'-map','0:v','-map','1:a','-c:a','aac','-b:a','192k','-shortest']
        cmd+=['-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-r',str(fps),'-movflags','+faststart',tmp]
        ff=subprocess.Popen(cmd,stdin=subprocess.PIPE);t0=time.time()
        last=n if end is None else int(end*fps)
        for i in range(int(start*fps),last):
            await p.evaluate(f"async()=>{{await render({i/fps});grain({i/fps})}}")
            ff.stdin.write(await p.screenshot(type='jpeg',quality=92))
        ff.stdin.close();rc=ff.wait()
        if rc==0:os.replace(tmp,out)
        print(out,'rc',rc,f'{time.time()-t0:.0f}s')
        await b.close()
async def stills(html,times,prefix):
    async with async_playwright() as pw:
        b=await pw.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--allow-file-access-from-files'])
        p=await (await b.new_context(viewport={'width':1080,'height':1920})).new_page();p.on('pageerror',lambda e:print('ERR',e))
        await p.goto('file://'+html);await p.evaluate("()=>window.__ready");await p.wait_for_timeout(400)
        for t in times:
            await p.evaluate(f"async()=>{{await render({t});grain({t})}}");await p.screenshot(path=f'{prefix}_{t:05.2f}.jpg',type='jpeg',quality=85)
        await b.close()
if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='stills':asyncio.run(stills(sys.argv[2],[float(x) for x in sys.argv[4:]],sys.argv[3]))
    else:asyncio.run(render(sys.argv[2],sys.argv[3],float(sys.argv[4]),audio=sys.argv[5] if len(sys.argv)>5 else None))
