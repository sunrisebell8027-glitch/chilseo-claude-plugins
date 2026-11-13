"""파일 읽기가 오래 걸릴 때 검사를 계속한다."""
import signal


def read_text(path):
    if not hasattr(signal, 'SIGALRM') or not hasattr(signal, 'alarm'):
        return path.read_text(encoding='utf-8')

    def timed_out(signum, frame):
        raise TimeoutError()

    previous = signal.signal(signal.SIGALRM, timed_out)
    signal.alarm(30)
    try:
        return path.read_text(encoding='utf-8')
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
