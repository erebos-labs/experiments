"""Recompute every displayed table using standard-library Python; no network."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from time import perf_counter
from model import summarize
from joint import conditional_summary, joint_eulerian
from cut_rules import compare

def rebuild():
    start = perf_counter()
    matrix = joint_eulerian(52)
    data = {
        'description': 'Exact ideal GSR riffles from the identity; all cards distinct',
        'convention': 'deck[position] = original zero-based card label',
        'method': 'Integer counts and exact fractions; JSON displays floating probabilities',
        'rows': [summarize(52, k) for k in range(15)],
        'typical_visible_condition': [
            {'k': k, **conditional_summary(matrix, 2**k, [25, 26])}
            for k in range(1, 13)],
        'small_gsr': [summarize(8, k, False) for k in range(13)],
    }
    for rule in ['half', 'uniform']:
        with redirect_stdout(io.StringIO()):
            result = compare(8, 12, rule, 120)
        if len(result['rows']) != 13:
            raise RuntimeError('Bounded enumeration did not finish; preserve the existing table')
        data['cut_'+rule] = [{key: value for key, value in row.items()
                            if key != 'elapsed_seconds'} for row in result['rows']]
    target = Path(__file__).with_name('data.json')
    target.write_text(json.dumps(data, separators=(',', ':'), allow_nan=False)+'\n')
    print(f'Rebuilt {target.name}: 15 full-deck rows, 12 conditional rows, 3 eight-card cut tables; {perf_counter()-start:.3f}s')

if __name__ == '__main__':
    rebuild()
