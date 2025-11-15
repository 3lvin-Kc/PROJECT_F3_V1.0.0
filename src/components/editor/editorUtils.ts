// Build a tree structure from the flat files map for the explorer
export const buildStructure = (filesMap: Record<string, string> | undefined) => {
  const root: any = { type: 'folder', name: '', children: [] as any[] };
  if (!filesMap) return [] as any[];
  for (const fullPath of Object.keys(filesMap)) {
    const parts = fullPath.split('/');
    let node = root;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isFile = i === parts.length - 1;
      if (isFile) {
        node.children.push({ type: 'file', name: part, path: fullPath });
      } else {
        let next = node.children.find((c: any) => c.type === 'folder' && c.name === part);
        if (!next) {
          next = { type: 'folder', name: part, children: [] as any[] };
          node.children.push(next);
        }
        node = next;
      }
    }
  }
  return root.children;
};

export const getFileLanguage = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'dart':
      return 'dart';
    case 'js':
      return 'javascript';
    case 'ts':
      return 'typescript';
    case 'jsx':
      return 'javascriptreact';
    case 'tsx':
      return 'typescriptreact';
    case 'html':
      return 'html';
    case 'css':
      return 'css';
    case 'scss':
      return 'scss';
    case 'yaml':
    case 'yml':
      return 'yaml';
    case 'json':
      return 'json';
    case 'md':
      return 'markdown';
    default:
      return 'plaintext';
  }
};