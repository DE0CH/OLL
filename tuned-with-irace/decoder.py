class IraceDecoder:
  def __init__(self):
    self.lines = []
  
  def note_line(self, line):
    if line.strip().startswith("# Best configurations as commandlines"):
      self.lines = []
    else:
      self.lines.append(line)
  
  def end(self):
    line = self.lines[0]
    line = line.strip().split()[1:]
    res = [float(line[i]) for i in range(len(line)) if i%2 == 1]
    if len(res) == 0:
      raise ValueError("res length is 0")
    return res
