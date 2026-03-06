/**
 * Sanitization Tests for XSS Vulnerability Fix
 *
 * Tests verify that:
 * 1. DOMPurify correctly blocks XSS payloads (script tags, event handlers, iframe, etc.)
 * 2. Safe markdown-generated HTML is preserved for rendering
 * 3. MarkdownContent component renders safely even with malicious API responses
 * 4. Edge cases (empty, unicode, mixed content) are handled correctly
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { sanitizeHtml, markdownToSafeHtml } from '@/lib/sanitize';

describe('sanitizeHtml() - Core XSS Prevention', () => {
  /**
   * AC1: Block script tag injection
   * Verifies common XSS attack via <script> tags is prevented
   */
  it('should strip script tags and alert() payloads', () => {
    const malicious = '<p>Hello <script>alert("XSS")</script></p>';
    const result = sanitizeHtml(malicious);

    // Script tag should be removed, content preserved
    expect(result).toContain('Hello');
    expect(result).not.toContain('script');
    expect(result).not.toContain('alert');
  });

  /**
   * AC2: Block event handler injection
   * Verifies img onerror and other inline event handlers are stripped
   */
  it('should remove event handlers like onerror, onclick, onload', () => {
    const payloads = [
      '<img src="x" onerror="alert(\'XSS\')">',
      '<div onclick="evil()">Click me</div>',
      '<body onload="alert(\'loaded\')">',
      '<svg onload="alert(1)">',
    ];

    payloads.forEach(payload => {
      const result = sanitizeHtml(payload);
      expect(result).not.toContain('onerror');
      expect(result).not.toContain('onclick');
      expect(result).not.toContain('onload');
    });
  });

  /**
   * AC3: Block iframe injection
   * Verifies iframe tags used for phishing/clickjacking are removed
   */
  it('should remove iframe tags completely', () => {
    const malicious = '<p>Content</p><iframe src="https://evil.com"></iframe>';
    const result = sanitizeHtml(malicious);

    expect(result).toContain('Content');
    expect(result).not.toContain('iframe');
  });

  /**
   * AC4: Allow safe markdown-generated tags
   * Verifies that h1, h2, h3, strong, em, code, p tags are preserved
   */
  it('should preserve safe markdown tags (h1, h2, strong, em, code, p)', () => {
    const safeHtml = '<h1>Title</h1><p>Content with <strong>bold</strong> and <em>italic</em></p>';
    const result = sanitizeHtml(safeHtml);

    expect(result).toContain('<h1>');
    expect(result).toContain('<strong>');
    expect(result).toContain('<em>');
    expect(result).toContain('<code>');
    expect(result).toContain('</h1>');
    expect(result).toContain('</strong>');
  });

  /**
   * Edge case: Data URIs should be blocked
   * Verifies SVG-based XSS via data URIs is prevented
   */
  it('should block data URIs that could enable XSS', () => {
    const dataUriXSS = '<img src="data:text/html,<script>alert(1)</script>">';
    const result = sanitizeHtml(dataUriXSS);

    // Data URI should be removed or neutered
    expect(result).not.toContain('alert');
    expect(result).not.toContain('script');
  });

  /**
   * Edge case: Empty string
   */
  it('should handle empty strings safely', () => {
    expect(sanitizeHtml('')).toBe('');
    expect(sanitizeHtml('   ')).toBeTruthy();
  });
});

describe('markdownToSafeHtml() - Markdown + Sanitization Pipeline', () => {
  /**
   * AC5: Convert markdown and sanitize in one step
   * Verifies the full pipeline: markdown regex → HTML → sanitize
   */
  it('should convert markdown headers and sanitize script injection', () => {
    const markdown = '# Title\n**bold** text';
    const result = markdownToSafeHtml(markdown);

    // Markdown should be converted
    expect(result).toContain('<h1');
    expect(result).toContain('<strong');

    // Should produce safe HTML
    expect(result).not.toContain('<script>');
  });

  /**
   * AC6: Block XSS in markdown-generated HTML
   * Verifies that if markdown conversion produces malicious HTML,
   * sanitization catches it
   */
  it('should sanitize markdown content even if it contains XSS payloads', () => {
    // User input with markdown + XSS attempt
    const userInput = '# Title\n**safe** <img src=x onerror="alert(1)">';
    const result = markdownToSafeHtml(userInput);

    expect(result).toContain('Title');
    expect(result).toContain('safe');
    expect(result).not.toContain('onerror');
    expect(result).not.toContain('alert');
  });

  /**
   * AC7: Preserve markdown formatting in sanitized output
   * Verifies bold, italic, code formatting is preserved
   */
  it('should preserve formatting: bold, italic, code, lists', () => {
    const markdown = `
## Section
- List item 1
- List item 2
**Bold text** and *italic text*
\`code block\`
    `.trim();

    const result = markdownToSafeHtml(markdown);

    expect(result).toContain('<h2');
    expect(result).toContain('<li');
    expect(result).toContain('<strong');
    expect(result).toContain('<em');
    expect(result).toContain('<code');
  });

  /**
   * Edge case: Complex markdown with nested formatting
   */
  it('should handle complex nested formatting without breaking', () => {
    const markdown = `
# Research Summary
**Key finding**: *Important data* from \`API response\`
- Point 1 with **emphasis**
- Point 2 with \`code\`
    `.trim();

    const result = markdownToSafeHtml(markdown);

    // Should not throw and should produce valid HTML
    expect(result).toBeTruthy();
    expect(result.length > 0).toBe(true);
    expect(result).toContain('h1');
  });

  /**
   * Edge case: Unicode and special characters
   */
  it('should preserve unicode characters and special symbols', () => {
    const markdown = '# Title with émojis 🚀\n**Price**: $100.50 → €95.00';
    const result = markdownToSafeHtml(markdown);

    expect(result).toContain('émojis');
    expect(result).toContain('🚀');
    expect(result).toContain('$');
    expect(result).toContain('→');
  });
});

describe('MarkdownContent Component - Integration', () => {
  /**
   * AC8: Component renders sanitized content safely
   * Verifies the React component correctly uses sanitization
   */
  it('should render safe markdown content without XSS', () => {
    // Dynamically import to avoid issues with 'use client'
    const { MarkdownContent } = require('@/app/research/page');

    const safeContent = '# Hello\n**World** is *beautiful*';
    render(<MarkdownContent content={safeContent} />);

    expect(screen.getByText(/Hello/)).toBeInTheDocument();
    expect(screen.getByText(/World/)).toBeInTheDocument();
  });

  /**
   * AC9: Component blocks injected scripts from API responses
   * Verifies that even if API returns malicious content,
   * it's rendered safely
   */
  it('should block script injection from API-sourced content', () => {
    const { MarkdownContent } = require('@/app/research/page');

    // Simulate API response with injected script
    const apiContent = '# Analysis\n**Data** <script>alert("hacked")</script>';

    const { container } = render(<MarkdownContent content={apiContent} />);

    // Script should not be in DOM
    expect(container.querySelector('script')).not.toBeInTheDocument();
    expect(screen.queryByText('hacked')).not.toBeInTheDocument();
  });

  /**
   * AC10: Component handles empty content
   */
  it('should render empty content without errors', () => {
    const { MarkdownContent } = require('@/app/research/page');

    const { container } = render(<MarkdownContent content="" />);
    expect(container.querySelector('div')).toBeInTheDocument();
  });
});

describe('XSS Vector Prevention - Real-World Payloads', () => {
  /**
   * Test common XSS payloads that attackers might try
   * Based on OWASP XSS Prevention Cheat Sheet
   */
  const xssPayloads = [
    {
      name: 'Basic script tag',
      payload: '<script>alert("XSS")</script>',
    },
    {
      name: 'Img with onerror',
      payload: '<img src=x onerror="alert(\'XSS\')">',
    },
    {
      name: 'SVG with onload',
      payload: '<svg onload="alert(\'XSS\')"></svg>',
    },
    {
      name: 'Body with onload',
      payload: '<body onload="alert(\'XSS\')"></body>',
    },
    {
      name: 'Link with javascript:',
      payload: '<a href="javascript:alert(\'XSS\')">Click</a>',
    },
    {
      name: 'Form with onfocus',
      payload: '<form onfocus="alert(\'XSS\')" autofocus>',
    },
    {
      name: 'Input with onmouseover',
      payload: '<input onmouseover="alert(\'XSS\')" type="text">',
    },
  ];

  xssPayloads.forEach(({ name, payload }) => {
    it(`should block: ${name}`, () => {
      const result = sanitizeHtml(payload);

      // Should not contain dangerous keywords
      expect(result).not.toContain('alert');
      expect(result).not.toContain('javascript:');
      expect(result).not.toContain('onerror');
      expect(result).not.toContain('onload');
      expect(result).not.toContain('onfocus');
      expect(result).not.toContain('onmouseover');
    });
  });
});
