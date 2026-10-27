"""Loopback-only static review server with byte ranges for video seeking."""
import argparse,functools,re
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

class ReviewHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        path=Path(self.translate_path(self.path))
        self.remaining=None
        if path.is_dir():
            for name in ('review.html','index.html'):
                if (path/name).is_file():path=path/name;break
            else:self.send_error(404);return None
        if not path.is_file():self.send_error(404);return None
        size=path.stat().st_size;start,end=0,size-1;partial=False
        value=self.headers.get('Range')
        if value:
            m=re.fullmatch(r'bytes=(\d*)-(\d*)',value.strip())
            if not m or not any(m.groups()):self.send_error(416);return None
            if m[1]:
                start=int(m[1]);end=min(int(m[2]) if m[2] else size-1,size-1)
            else:start=max(0,size-int(m[2]));end=size-1
            if not 0<=start<=end<size:
                self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.end_headers();return None
            partial=True
        stream=path.open('rb');stream.seek(start);self.remaining=end-start+1
        self.send_response(206 if partial else 200)
        self.send_header('Content-Type',self.guess_type(str(path)))
        self.send_header('Content-Length',str(self.remaining))
        self.send_header('Accept-Ranges','bytes')
        self.send_header('Cache-Control','no-cache')
        if partial:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers();return stream

    def copyfile(self,source,output):
        remaining=self.remaining
        try:
            while remaining>0:
                data=source.read(min(65536,remaining))
                if not data:break
                output.write(data);remaining-=len(data)
        except (BrokenPipeError,ConnectionAbortedError,ConnectionResetError):pass

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8878)
    parser.add_argument('--directory',type=Path,default=Path(__file__).resolve().parents[1]/'outputs/facility_dataset/temporal_pipeline/sequence_annotation_v4')
    args=parser.parse_args()
    handler=functools.partial(ReviewHandler,directory=str(args.directory.resolve()))
    ThreadingHTTPServer(('127.0.0.1',args.port),handler).serve_forever()

if __name__=='__main__':main()
