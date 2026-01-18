import { Hono } from 'hono';
import type { ManagedTransaction } from 'neo4j-driver';
import { getSession, neo4j } from '../db/neo4j';
import type { ConversationMessage } from '@rewind/shared';

const app = new Hono();

interface IngestPayload {
  projectId: string;
  projectPath: string;
  conversationId: string;
  message: ConversationMessage;
}

interface BatchIngestPayload {
  projectId: string;
  projectPath: string;
  conversationId: string;
  messages: ConversationMessage[];
}

/**
 * Ingest a single message into Neo4j (shared logic for both endpoints)
 */
async function ingestMessage(
  tx: ManagedTransaction,
  conversationId: string,
  message: ConversationMessage
): Promise<void> {
  // Extract usage info
  const usage =
    message.type === 'assistant' && 'usage' in message.message
      ? (message.message as { usage?: { input_tokens?: number; output_tokens?: number } }).usage
      : undefined;

  // Create message node
  await tx.run(
    `
    MATCH (c:Rewind_Conversation {sessionId: $conversationId})
    MERGE (m:Rewind_Message {uuid: $uuid})
    ON CREATE SET m.type = $type,
                  m.timestamp = $timestamp,
                  m.parentUuid = $parentUuid,
                  m.isSidechain = $isSidechain,
                  m.userType = $userType,
                  m.cwd = $cwd,
                  m.sessionId = $sessionId,
                  m.version = $version,
                  m.gitBranch = $gitBranch,
                  m.agentId = $agentId,
                  m.requestId = $requestId,
                  m.model = $model,
                  m.inputTokens = $inputTokens,
                  m.outputTokens = $outputTokens,
                  m.messageData = $messageData,
                  m.preview = $preview,
                  m.createdAt = datetime()
    MERGE (c)-[:CONTAINS]->(m)
    `,
    {
      conversationId,
      uuid: message.uuid,
      type: message.type,
      timestamp: message.timestamp,
      parentUuid: message.parentUuid,
      isSidechain: message.isSidechain || false,
      userType: message.userType || null,
      cwd: message.cwd || null,
      sessionId: message.sessionId,
      version: message.version,
      gitBranch: message.gitBranch || null,
      agentId: message.agentId || null,
      requestId: message.requestId || null,
      model:
        message.type === 'assistant' && 'model' in message.message
          ? (message.message as { model?: string }).model
          : null,
      inputTokens: usage?.input_tokens ? neo4j.int(usage.input_tokens) : null,
      outputTokens: usage?.output_tokens ? neo4j.int(usage.output_tokens) : null,
      messageData: JSON.stringify(message.message),
      preview: getPreview(message),
    }
  );

  // Create content block nodes for assistant messages
  // We use MERGE to avoid duplicate content blocks on re-ingestion
  if (
    message.type === 'assistant' &&
    'content' in message.message &&
    Array.isArray((message.message as { content?: unknown[] }).content)
  ) {
    const content = (message.message as { content: unknown[] }).content;
    for (let i = 0; i < content.length; i++) {
      const block = content[i] as Record<string, unknown>;
      await tx.run(
        `
        MATCH (m:Rewind_Message {uuid: $messageUuid})
        MERGE (m)-[:HAS_BLOCK]->(b:Rewind_ContentBlock {messageUuid: $messageUuid, index: $index})
        ON CREATE SET b.type = $type,
                      b.data = $data
        `,
        {
          messageUuid: message.uuid,
          index: neo4j.int(i),
          type: block.type || 'unknown',
          data: JSON.stringify(block),
        }
      );
    }
  }
}

/**
 * Ensure project and conversation exist in Neo4j
 */
async function ensureProjectAndConversation(
  tx: ManagedTransaction,
  projectId: string,
  projectPath: string,
  conversationId: string,
  firstMessage: ConversationMessage
): Promise<void> {
  // Ensure project exists
  await tx.run(
    `
    MERGE (p:Rewind_Project {id: $projectId})
    ON CREATE SET p.path = $projectPath,
                  p.name = $projectId,
                  p.displayName = $projectId,
                  p.createdAt = datetime()
    `,
    { projectId, projectPath }
  );

  // Ensure conversation exists
  await tx.run(
    `
    MATCH (p:Rewind_Project {id: $projectId})
    MERGE (c:Rewind_Conversation {sessionId: $conversationId})
    ON CREATE SET c.uuid = $uuid,
                  c.timestamp = datetime($timestamp),
                  c.createdAt = datetime()
    MERGE (p)-[:HAS_CONVERSATION]->(c)
    `,
    {
      projectId,
      conversationId,
      uuid: firstMessage.uuid,
      timestamp: firstMessage.timestamp,
    }
  );
}

// POST /api/ingest/batch - Ingest multiple messages in a single request (preferred)
app.post('/batch', async (c) => {
  try {
    const payload: BatchIngestPayload = await c.req.json();
    const { projectId, projectPath, conversationId, messages } = payload;

    if (!projectId || !conversationId || !messages || !Array.isArray(messages)) {
      return c.json({ error: 'Missing required fields' }, 400);
    }

    if (messages.length === 0) {
      return c.json({ success: true, ingested: 0 });
    }

    const session = getSession();
    try {
      await session.executeWrite(async (tx) => {
        // Ensure project and conversation exist (once for all messages)
        await ensureProjectAndConversation(tx, projectId, projectPath, conversationId, messages[0]);

        // Process all messages in the same transaction
        for (const message of messages) {
          await ingestMessage(tx, conversationId, message);
        }
      });

      return c.json({ success: true, ingested: messages.length });
    } finally {
      await session.close();
    }
  } catch (error) {
    console.error('Error batch ingesting messages:', error);
    return c.json({ error: 'Failed to ingest messages' }, 500);
  }
});

// POST /api/ingest - Ingest a single message from hook (legacy, still supported)
app.post('/', async (c) => {
  try {
    const payload: IngestPayload = await c.req.json();
    const { projectId, projectPath, conversationId, message } = payload;

    if (!projectId || !conversationId || !message) {
      return c.json({ error: 'Missing required fields' }, 400);
    }

    const session = getSession();
    try {
      await session.executeWrite(async (tx) => {
        await ensureProjectAndConversation(tx, projectId, projectPath, conversationId, message);
        await ingestMessage(tx, conversationId, message);
      });

      return c.json({ success: true });
    } finally {
      await session.close();
    }
  } catch (error) {
    console.error('Error ingesting message:', error);
    return c.json({ error: 'Failed to ingest message' }, 500);
  }
});

function getPreview(message: ConversationMessage): string {
  if (message.type === 'user') {
    const content = message.message.content;
    if (typeof content === 'string') {
      return content.slice(0, 200);
    }
    if (Array.isArray(content)) {
      const textBlock = content.find(
        (b): b is { type: 'text'; text: string } =>
          typeof b === 'object' && b !== null && 'type' in b && b.type === 'text'
      );
      return textBlock?.text?.slice(0, 200) || '';
    }
  }
  if (message.type === 'assistant' && 'content' in message.message) {
    const content = (message.message as { content?: unknown[] }).content;
    if (Array.isArray(content)) {
      const textBlock = content.find(
        (b): b is { type: 'text'; text: string } =>
          typeof b === 'object' && b !== null && 'type' in b && b.type === 'text'
      );
      return textBlock?.text?.slice(0, 200) || '';
    }
  }
  return '';
}

export default app;
