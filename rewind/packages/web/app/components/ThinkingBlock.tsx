import { useState } from 'react';
import { ChevronDown, Copy, Check } from 'lucide-react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { Button } from './ui/button';
import type { ThinkingBlock as ThinkingBlockType } from '~/lib/types';
import { log } from '~/lib/logger';

interface ThinkingBlockProps {
  block: ThinkingBlockType;
}

const THINKING_PREVIEW_LENGTH = 120; // Characters to show in preview
const COPY_FEEDBACK_DURATION_MS = 2000; // Duration to show copy confirmation

export function ThinkingBlock({ block }: ThinkingBlockProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(block.thinking).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), COPY_FEEDBACK_DURATION_MS);
    }).catch((error) => {
      log.error('Failed to copy to clipboard:', error);
    });
  };

  const preview = block.thinking.length > THINKING_PREVIEW_LENGTH
    ? block.thinking.slice(0, THINKING_PREVIEW_LENGTH) + '...'
    : block.thinking;

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className="my-2">
      <div className="flex items-center gap-2">
        <CollapsibleTrigger asChild>
          <button className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
            <ChevronDown className={`h-3 w-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            <span className="italic">Thinking</span>
          </button>
        </CollapsibleTrigger>
        <Button
          variant="ghost"
          size="sm"
          className="h-5 w-5 p-0 opacity-0 hover:opacity-100 focus:opacity-100 transition-opacity"
          onClick={handleCopy}
        >
          {copied ? (
            <Check className="h-3 w-3 text-muted-foreground" />
          ) : (
            <Copy className="h-3 w-3 text-muted-foreground" />
          )}
        </Button>
      </div>
      <CollapsibleContent>
        <p className="text-sm text-muted-foreground italic leading-relaxed mt-1 pl-5">
          {block.thinking}
        </p>
      </CollapsibleContent>
      {!isOpen && block.thinking.length > THINKING_PREVIEW_LENGTH && (
        <p className="text-sm text-muted-foreground/60 italic leading-relaxed mt-1 pl-5 line-clamp-2">
          {preview}
        </p>
      )}
    </Collapsible>
  );
}
