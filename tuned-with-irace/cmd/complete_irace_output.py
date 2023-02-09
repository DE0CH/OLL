import argparse

parser = argparse.ArgumentParser()
parser.add_argument('in_file')
parser.add_argument('out_file')
parser.add_argument('lbds', nargs='+')
args = parser.parse_args()

def complete_partial_progress_with_file(infile, outfile, lbd_values):
  og = infile.read() #FIXME: Don't just load the entire file into memory because that's slow.
  og = '# NOTE: THIS FILE IS EDITED. It is not entirely from the output of irace, but because irace was stuck, I manually edited the file so that the subsequent steps of the automated script can continue\n' + og
  command_args = []
  for i, lbd in enumerate(lbd_values):
    command_args.append(f'--lbd{i}')
    command_args.append(f'{lbd}')
  end_lines = [
    '',
    '# The lines below are not output from irace, but rather manually edited so that that subsequent steps of the automated script can successfully detect and parse the data.',
    '',
    '# Best configurations as commandlines (first number is the configuration ID; same order as above):',
    '1 ' + ' '.join(command_args),
    ''
  ]

  outfile.write(og + '\n'.join(end_lines))

if __name__ == '__main__':
    with open(args.in_file) as in_file:
       with open(args.out_file, 'w') as out_file:
          complete_partial_progress_with_file(in_file, out_file, args.lbds)