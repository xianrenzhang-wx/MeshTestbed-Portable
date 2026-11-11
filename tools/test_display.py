"""Exercise the real OpenGL viewer with bounded frames and saved evidence."""
import argparse
import json
from pathlib import Path
import numpy as np
import polyscope as ps
from mesh_testbed import Mesh

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    model=Path(__file__).resolve().parents[2]/'MeshTestbed_C++/STLs/Cow.stl'
    original_show=ps.show
    ps.set_use_prefs_file(False)
    # Keep actual rendering and Mesh.show(), only bound the interactive wait.
    calls=[]
    def bounded_show():
        ps.set_window_size(960,720)
        ps.set_ui_scale(0.5)
        original_show(forFrames=8)
        screenshot=out/f'display-{len(calls)+1}.png'
        ps.screenshot(str(screenshot),transparent_bg=False,include_UI=True)
        pixels=ps.screenshot_to_buffer(transparent_bg=False,include_UI=False)
        assert np.std(pixels[:,:,:3])>5, 'Rendered image is unexpectedly blank'
        calls.append({'screenshot':screenshot.name,'shape':list(pixels.shape),
                      'pixel_std':float(np.std(pixels[:,:,:3])), 'backend':ps.get_render_engine_backend_name()})
    ps.show=bounded_show
    try:
        with Mesh(model) as mesh:
            mesh.show()
            mesh.rotate('z',.5)
            mesh.show()
        assert len(calls)==2
        assert all('mock' not in item['backend'].lower() for item in calls)
        report={'status':'passed','polyscope':ps.__version__,'numpy':np.__version__,
                'model':str(model),'calls':calls,
                'scope':'Real Mesh.show and OpenGL frame rendering; bounded show(forFrames=8). Mouse/keyboard interaction not automated.'}
        (out/'display.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report,indent=2))
    finally:
        ps.show=original_show
        if ps.is_initialized():ps.shutdown()

if __name__=='__main__':main()
