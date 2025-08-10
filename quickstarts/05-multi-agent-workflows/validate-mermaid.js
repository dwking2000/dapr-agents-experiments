#!/usr/bin/env node

// Simple Mermaid syntax validator
function validateMermaidSyntax(content) {
    const errors = [];
    const lines = content.split('\n');
    
    // Check for common syntax errors
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        const lineNum = i + 1;
        
        // Check for bullet points (•) - causes "unsupported markdown:list" 
        if (line.includes('•')) {
            errors.push(`Line ${lineNum}: Contains bullet point (•) - replace with plain text`);
        }
        
        // Check for pipe characters in node labels (causes parse errors)
        // But ignore edge labels (lines with --> or -.->)
        if (line.includes('[') && line.includes('|') && !line.includes('-->') && !line.includes('-.->')) {
            errors.push(`Line ${lineNum}: Contains pipe (|) in node label - use commas instead`);
        }
        
        // Check for function calls with parentheses in node labels  
        if (line.includes('[') && /\w+\(\)/.test(line)) {
            errors.push(`Line ${lineNum}: Contains function call syntax - use plain description instead`);
        }
        
        // Check for numbered lists (1. 2. 3.)
        if (/\d+\.\s/.test(line) && line.includes('[')) {
            errors.push(`Line ${lineNum}: Contains numbered list - use plain descriptive text`);
        }
    }
    
    return errors;
}

// Read from stdin or file
const fs = require('fs');
const input = process.argv[2];

if (!input) {
    console.log('Usage: node validate-mermaid.js <mermaid-content-or-file>');
    process.exit(1);
}

let content;
if (fs.existsSync(input)) {
    content = fs.readFileSync(input, 'utf8');
} else {
    content = input;
}

const errors = validateMermaidSyntax(content);

if (errors.length === 0) {
    console.log('✅ No common Mermaid syntax issues found!');
    process.exit(0);
} else {
    console.log('❌ Found potential Mermaid syntax issues:');
    errors.forEach(error => console.log(`  - ${error}`));
    process.exit(1);
}