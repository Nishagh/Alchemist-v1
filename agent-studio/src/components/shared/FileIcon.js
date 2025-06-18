/**
 * File Icon Component
 * 
 * Returns appropriate Material-UI icons based on file extensions
 */
import React from 'react';
import {
  InsertDriveFile as DefaultFileIcon,
  Description as DocumentIcon,
  Code as CodeIcon,
  Image as ImageIcon,
  PictureAsPdf as PdfIcon,
  TableChart as SpreadsheetIcon,
  Slideshow as PresentationIcon,
  Archive as ArchiveIcon,
  VideoFile as VideoIcon,
  AudioFile as AudioIcon,
  DataObject as JsonIcon,
  Language as HtmlIcon,
  Css as CssIcon
} from '@mui/icons-material';

/**
 * Get file type from filename extension
 */
export const getFileTypeFromName = (filename) => {
  if (!filename) return 'Unknown';
  
  const extension = filename.split('.').pop()?.toLowerCase();
  
  const typeMap = {
    // Documents
    'pdf': 'PDF Document',
    'doc': 'Word Document',
    'docx': 'Word Document',
    'txt': 'Text Document',
    'rtf': 'Rich Text Document',
    'md': 'Markdown Document',
    'markdown': 'Markdown Document',
    
    // Spreadsheets
    'xls': 'Excel Spreadsheet',
    'xlsx': 'Excel Spreadsheet',
    'csv': 'CSV File',
    'ods': 'OpenOffice Spreadsheet',
    
    // Presentations
    'ppt': 'PowerPoint Presentation',
    'pptx': 'PowerPoint Presentation',
    'odp': 'OpenOffice Presentation',
    
    // Code files
    'js': 'JavaScript File',
    'jsx': 'React Component',
    'ts': 'TypeScript File',
    'tsx': 'TypeScript React Component',
    'py': 'Python Script',
    'java': 'Java File',
    'cpp': 'C++ File',
    'c': 'C File',
    'h': 'Header File',
    'css': 'CSS Stylesheet',
    'scss': 'SASS Stylesheet',
    'less': 'LESS Stylesheet',
    'html': 'HTML Document',
    'htm': 'HTML Document',
    'xml': 'XML Document',
    'json': 'JSON Data',
    'yaml': 'YAML Configuration',
    'yml': 'YAML Configuration',
    'toml': 'TOML Configuration',
    'ini': 'Configuration File',
    'env': 'Environment File',
    'sql': 'SQL Script',
    'sh': 'Shell Script',
    'bash': 'Bash Script',
    'bat': 'Batch Script',
    'ps1': 'PowerShell Script',
    
    // Images
    'jpg': 'JPEG Image',
    'jpeg': 'JPEG Image',
    'png': 'PNG Image',
    'gif': 'GIF Image',
    'bmp': 'Bitmap Image',
    'svg': 'SVG Vector Image',
    'webp': 'WebP Image',
    'ico': 'Icon File',
    
    // Archives
    'zip': 'ZIP Archive',
    'rar': 'RAR Archive',
    '7z': '7-Zip Archive',
    'tar': 'TAR Archive',
    'gz': 'Gzip Archive',
    'bz2': 'Bzip2 Archive',
    
    // Audio/Video
    'mp3': 'MP3 Audio',
    'mp4': 'MP4 Video',
    'avi': 'AVI Video',
    'mov': 'QuickTime Video',
    'wmv': 'Windows Media Video',
    'flv': 'Flash Video',
    'webm': 'WebM Video',
    'wav': 'WAV Audio',
    'ogg': 'OGG Audio',
    'flac': 'FLAC Audio',
    
    // Other
    'log': 'Log File',
    'backup': 'Backup File',
    'tmp': 'Temporary File',
    'cache': 'Cache File'
  };
  
  return typeMap[extension] || `${extension?.toUpperCase() || 'Unknown'} File`;
};

/**
 * Get appropriate icon for file type
 */
export const getFileIcon = (filename, iconProps = {}) => {
  if (!filename) return <DefaultFileIcon {...iconProps} />;
  
  const extension = filename.split('.').pop()?.toLowerCase();
  
  // Code files
  if (['js', 'jsx', 'ts', 'tsx', 'py', 'java', 'cpp', 'c', 'h', 'php', 'rb', 'go', 'rs', 'kt', 'swift'].includes(extension)) {
    return <CodeIcon {...iconProps} />;
  }
  
  // Web files
  if (extension === 'html' || extension === 'htm') {
    return <HtmlIcon {...iconProps} />;
  }
  
  if (extension === 'css' || extension === 'scss' || extension === 'less') {
    return <CssIcon {...iconProps} />;
  }
  
  if (extension === 'js' || extension === 'jsx') {
    return <CodeIcon {...iconProps} />;
  }
  
  // Data files
  if (['json', 'xml', 'yaml', 'yml', 'toml'].includes(extension)) {
    return <JsonIcon {...iconProps} />;
  }
  
  // Documents
  if (['pdf'].includes(extension)) {
    return <PdfIcon {...iconProps} />;
  }
  
  if (['doc', 'docx', 'txt', 'rtf', 'md', 'markdown'].includes(extension)) {
    return <DocumentIcon {...iconProps} />;
  }
  
  // Spreadsheets
  if (['xls', 'xlsx', 'csv', 'ods'].includes(extension)) {
    return <SpreadsheetIcon {...iconProps} />;
  }
  
  // Presentations
  if (['ppt', 'pptx', 'odp'].includes(extension)) {
    return <PresentationIcon {...iconProps} />;
  }
  
  // Images
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico'].includes(extension)) {
    return <ImageIcon {...iconProps} />;
  }
  
  // Archives
  if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2'].includes(extension)) {
    return <ArchiveIcon {...iconProps} />;
  }
  
  // Video
  if (['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'].includes(extension)) {
    return <VideoIcon {...iconProps} />;
  }
  
  // Audio
  if (['mp3', 'wav', 'ogg', 'flac'].includes(extension)) {
    return <AudioIcon {...iconProps} />;
  }
  
  // Default
  return <DefaultFileIcon {...iconProps} />;
};

const FileIcon = ({ filename, ...iconProps }) => {
  return getFileIcon(filename, iconProps);
};

export default FileIcon;