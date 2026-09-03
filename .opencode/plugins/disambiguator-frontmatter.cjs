'use strict';

// Disambiguator command-file frontmatter parser for OpenCode.
//
// Kept in a separate CommonJS helper so that disambiguator.mjs only exports
// a single default plugin function. OpenCode's legacy plugin loader treats
// every exported function from the main plugin entry as a plugin hook.

const fs = require('fs');

function parseCommandFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  // Tolerate CRLF and LF: Windows checkouts deliver \r\n, npm/linux ship \n.
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  if (!match) return null;
  const description = match[1].match(/description:\s*(.+)/)?.[1]?.trim();
  return { description, template: match[2].trim() };
}

module.exports = { parseCommandFile };
