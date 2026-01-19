import { getSession, neo4j } from './neo4j';
import type { Project, Conversation, ConversationMessage, Stats } from '@rewind/shared';

// Helper to convert Neo4j integers to JS numbers
function toNumber(value: unknown): number {
  if (neo4j.isInt(value)) {
    return (value as ReturnType<typeof neo4j.int>).toNumber();
  }
  return typeof value === 'number' ? value : 0;
}

// Helper to convert Neo4j datetime to JS Date
function toDate(value: unknown): Date {
  if (value && typeof value === 'object' && 'toStandardDate' in value) {
    return (value as { toStandardDate: () => Date }).toStandardDate();
  }
  return value instanceof Date ? value : new Date(String(value));
}

export async function getProjects(): Promise<Project[]> {
  const session = getSession();
  try {
    const result = await session.executeRead(async (tx) => {
      return tx.run(`
        MATCH (p:Rewind_Project)
        OPTIONAL MATCH (p)-[:HAS_CONVERSATION]->(c:Rewind_Conversation)
        WITH p, count(c) as convCount, max(c.timestamp) as lastMod
        OPTIONAL MATCH (p)-[:HAS_CONVERSATION]->(:Rewind_Conversation)-[:CONTAINS]->(m:Rewind_Message)
        RETURN p.id as id,
               p.name as name,
               p.displayName as displayName,
               p.path as path,
               convCount as conversationCount,
               count(m) as totalMessages,
               lastMod as lastModified
        ORDER BY lastMod DESC
      `);
    });

    return result.records.map((record) => ({
      id: record.get('id'),
      name: record.get('name'),
      displayName: record.get('displayName') || record.get('name') || record.get('id'),
      path: record.get('path'),
      conversationCount: toNumber(record.get('conversationCount')),
      totalMessages: toNumber(record.get('totalMessages')),
      lastModified: toDate(record.get('lastModified')),
    }));
  } finally {
    await session.close();
  }
}

export async function getProject(projectId: string): Promise<Project | null> {
  const session = getSession();
  try {
    const result = await session.executeRead(async (tx) => {
      return tx.run(
        `
        MATCH (p:Rewind_Project {id: $projectId})
        OPTIONAL MATCH (p)-[:HAS_CONVERSATION]->(c:Rewind_Conversation)
        WITH p, count(c) as convCount, max(c.timestamp) as lastMod
        OPTIONAL MATCH (p)-[:HAS_CONVERSATION]->(:Rewind_Conversation)-[:CONTAINS]->(m:Rewind_Message)
        RETURN p.id as id,
               p.name as name,
               p.displayName as displayName,
               p.path as path,
               convCount as conversationCount,
               count(m) as totalMessages,
               lastMod as lastModified
      `,
        { projectId }
      );
    });

    if (result.records.length === 0) return null;

    const record = result.records[0];
    return {
      id: record.get('id'),
      name: record.get('name'),
      displayName: record.get('displayName') || record.get('name') || record.get('id'),
      path: record.get('path'),
      conversationCount: toNumber(record.get('conversationCount')),
      totalMessages: toNumber(record.get('totalMessages')),
      lastModified: toDate(record.get('lastModified')),
    };
  } finally {
    await session.close();
  }
}

export async function getProjectConversations(projectId: string): Promise<Conversation[]> {
  const session = getSession();
  try {
    const result = await session.executeRead(async (tx) => {
      return tx.run(
        `
        MATCH (p:Rewind_Project {id: $projectId})-[:HAS_CONVERSATION]->(c:Rewind_Conversation)
        OPTIONAL MATCH (c)-[:CONTAINS]->(m:Rewind_Message)
        WITH c, count(m) as msgCount,
             collect(m)[0] as firstMsg,
             sum(COALESCE(m.inputTokens, 0)) as inputTokens,
             sum(COALESCE(m.outputTokens, 0)) as outputTokens
        RETURN c.sessionId as sessionId,
               c.uuid as uuid,
               c.timestamp as timestamp,
               msgCount as messageCount,
               COALESCE(firstMsg.preview, '') as preview,
               COALESCE(firstMsg.type, 'user') as type,
               firstMsg.model as model,
               inputTokens,
               outputTokens
        ORDER BY c.timestamp DESC
      `,
        { projectId }
      );
    });

    return result.records.map((record) => ({
      sessionId: record.get('sessionId'),
      uuid: record.get('uuid'),
      timestamp: toDate(record.get('timestamp')),
      messageCount: toNumber(record.get('messageCount')),
      preview: record.get('preview') || '',
      type: record.get('type') || 'user',
      model: record.get('model'),
      inputTokens: toNumber(record.get('inputTokens')),
      outputTokens: toNumber(record.get('outputTokens')),
      totalTokens: toNumber(record.get('inputTokens')) + toNumber(record.get('outputTokens')),
      messages: [],
    }));
  } finally {
    await session.close();
  }
}

export async function getConversation(conversationId: string): Promise<Conversation | null> {
  const session = getSession();
  try {
    // Get conversation metadata including enterprise fields
    const convResult = await session.executeRead(async (tx) => {
      return tx.run(
        `
        MATCH (c:Rewind_Conversation {sessionId: $conversationId})
        RETURN c.sessionId as sessionId,
               c.uuid as uuid,
               c.timestamp as timestamp,
               c.hostname as hostname,
               c.ipAddress as ipAddress,
               c.username as username,
               c.platform as platform,
               c.osVersion as osVersion,
               c.team as team,
               c.environment as environment
      `,
        { conversationId }
      );
    });

    if (convResult.records.length === 0) return null;

    const convRecord = convResult.records[0];

    // Get messages with content blocks
    const msgResult = await session.executeRead(async (tx) => {
      return tx.run(
        `
        MATCH (c:Rewind_Conversation {sessionId: $conversationId})-[:CONTAINS]->(m:Rewind_Message)
        OPTIONAL MATCH (m)-[:HAS_BLOCK]->(b:Rewind_ContentBlock)
        WITH m, collect(b {.*}) as blocks
        ORDER BY m.timestamp ASC
        RETURN m {
          .uuid,
          .type,
          .timestamp,
          .parentUuid,
          .isSidechain,
          .userType,
          .cwd,
          .sessionId,
          .version,
          .gitBranch,
          .agentId,
          .requestId,
          .inputTokens,
          .outputTokens,
          .model,
          .messageData
        } as message, blocks
      `,
        { conversationId }
      );
    });

    const messages: ConversationMessage[] = msgResult.records.map((record) => {
      const m = record.get('message');
      const blocks = record.get('blocks') || [];

      // Parse the stored message data or reconstruct from node properties
      let messageData = m.messageData ? JSON.parse(m.messageData) : null;

      if (!messageData) {
        // Reconstruct message structure
        if (m.type === 'assistant') {
          messageData = {
            model: m.model || 'unknown',
            id: m.uuid,
            type: 'message',
            role: 'assistant',
            content: blocks.map((b: Record<string, unknown>) => b),
            stop_reason: 'end_turn',
            stop_sequence: null,
            usage: {
              input_tokens: toNumber(m.inputTokens),
              output_tokens: toNumber(m.outputTokens),
            },
          };
        } else {
          messageData = {
            role: 'user',
            content: blocks.length > 0 ? blocks : '',
          };
        }
      }

      return {
        uuid: m.uuid,
        type: m.type,
        timestamp: m.timestamp,
        parentUuid: m.parentUuid,
        isSidechain: m.isSidechain,
        userType: m.userType,
        cwd: m.cwd,
        sessionId: m.sessionId,
        version: m.version,
        gitBranch: m.gitBranch,
        agentId: m.agentId,
        requestId: m.requestId,
        message: messageData,
        usage: m.inputTokens
          ? {
              input_tokens: toNumber(m.inputTokens),
              output_tokens: toNumber(m.outputTokens),
            }
          : undefined,
      };
    });

    // Calculate totals
    const inputTokens = messages.reduce((sum, m) => sum + (m.usage?.input_tokens || 0), 0);
    const outputTokens = messages.reduce((sum, m) => sum + (m.usage?.output_tokens || 0), 0);

    // Extract preview from first user message
    const firstUserMsg = messages.find((m) => m.type === 'user');
    let preview = '';
    if (firstUserMsg?.message?.content) {
      const content = firstUserMsg.message.content;
      if (typeof content === 'string') {
        preview = content.slice(0, 200);
      } else if (Array.isArray(content)) {
        const textBlock = content.find((b: { type: string }) => b.type === 'text');
        if (textBlock && 'text' in textBlock) {
          preview = (textBlock as { text: string }).text.slice(0, 200);
        }
      }
    }

    return {
      sessionId: convRecord.get('sessionId'),
      uuid: convRecord.get('uuid'),
      timestamp: toDate(convRecord.get('timestamp')),
      messageCount: messages.length,
      preview,
      type: messages[0]?.type || 'user',
      model: (() => {
        const assistantMsg = messages.find((m) => m.type === 'assistant');
        return assistantMsg && 'model' in assistantMsg.message ? assistantMsg.message.model : undefined;
      })(),
      messages,
      inputTokens,
      outputTokens,
      totalTokens: inputTokens + outputTokens,
      // Enterprise metadata
      hostname: convRecord.get('hostname') || undefined,
      ipAddress: convRecord.get('ipAddress') || undefined,
      username: convRecord.get('username') || undefined,
      platform: convRecord.get('platform') || undefined,
      osVersion: convRecord.get('osVersion') || undefined,
      team: convRecord.get('team') || undefined,
      environment: convRecord.get('environment') || undefined,
    };
  } finally {
    await session.close();
  }
}

export async function getRecentConversations(limit = 20): Promise<(Conversation & { projectId: string; starred?: boolean })[]> {
  const session = getSession();
  try {
    const result = await session.executeRead(async (tx) => {
      return tx.run(
        `
        MATCH (p:Rewind_Project)-[:HAS_CONVERSATION]->(c:Rewind_Conversation)
        OPTIONAL MATCH (c)-[:CONTAINS]->(m:Rewind_Message)
        WITH p, c, count(m) as msgCount,
             collect(m)[0] as firstMsg,
             sum(COALESCE(m.inputTokens, 0)) as inputTokens,
             sum(COALESCE(m.outputTokens, 0)) as outputTokens
        RETURN p.id as projectId,
               c.sessionId as sessionId,
               c.uuid as uuid,
               c.timestamp as timestamp,
               COALESCE(c.starred, false) as starred,
               msgCount as messageCount,
               COALESCE(firstMsg.preview, '') as preview,
               COALESCE(firstMsg.type, 'user') as type,
               firstMsg.model as model,
               inputTokens,
               outputTokens,
               c.hostname as hostname,
               c.ipAddress as ipAddress,
               c.username as username,
               c.team as team,
               c.environment as environment
        ORDER BY c.starred DESC, c.timestamp DESC
        LIMIT $limit
      `,
        { limit: neo4j.int(limit) }
      );
    });

    return result.records.map((record) => ({
      projectId: record.get('projectId'),
      sessionId: record.get('sessionId'),
      uuid: record.get('uuid'),
      timestamp: toDate(record.get('timestamp')),
      starred: record.get('starred') || false,
      messageCount: toNumber(record.get('messageCount')),
      preview: record.get('preview') || '',
      type: record.get('type') || 'user',
      model: record.get('model'),
      inputTokens: toNumber(record.get('inputTokens')),
      outputTokens: toNumber(record.get('outputTokens')),
      totalTokens: toNumber(record.get('inputTokens')) + toNumber(record.get('outputTokens')),
      messages: [],
      // Enterprise metadata
      hostname: record.get('hostname') || undefined,
      ipAddress: record.get('ipAddress') || undefined,
      username: record.get('username') || undefined,
      team: record.get('team') || undefined,
      environment: record.get('environment') || undefined,
    }));
  } finally {
    await session.close();
  }
}

export async function toggleConversationStar(sessionId: string): Promise<boolean> {
  const session = getSession();
  try {
    const result = await session.executeWrite(async (tx) => {
      return tx.run(
        `
        MATCH (c:Rewind_Conversation {sessionId: $sessionId})
        SET c.starred = NOT COALESCE(c.starred, false)
        RETURN c.starred as starred
      `,
        { sessionId }
      );
    });

    if (result.records.length === 0) {
      throw new Error('Conversation not found');
    }

    return result.records[0].get('starred');
  } finally {
    await session.close();
  }
}

export async function searchConversations(
  query: string,
  projectId?: string
): Promise<Conversation[]> {
  const session = getSession();
  try {
    const cypher = projectId
      ? `
        MATCH (p:Rewind_Project {id: $projectId})-[:HAS_CONVERSATION]->(c:Rewind_Conversation)-[:CONTAINS]->(m:Rewind_Message)
        WHERE m.preview CONTAINS $query OR m.messageData CONTAINS $query
        WITH DISTINCT c, max(m.timestamp) as lastMsg
        RETURN c.sessionId as sessionId,
               c.uuid as uuid,
               c.timestamp as timestamp
        ORDER BY lastMsg DESC
        LIMIT 50
      `
      : `
        MATCH (c:Rewind_Conversation)-[:CONTAINS]->(m:Rewind_Message)
        WHERE m.preview CONTAINS $query OR m.messageData CONTAINS $query
        WITH DISTINCT c, max(m.timestamp) as lastMsg
        RETURN c.sessionId as sessionId,
               c.uuid as uuid,
               c.timestamp as timestamp
        ORDER BY lastMsg DESC
        LIMIT 50
      `;

    const result = await session.executeRead(async (tx) => {
      return tx.run(cypher, { query, projectId });
    });

    return result.records.map((record) => ({
      sessionId: record.get('sessionId'),
      uuid: record.get('uuid'),
      timestamp: toDate(record.get('timestamp')),
      messageCount: 0,
      preview: '',
      type: 'user' as const,
      messages: [],
    }));
  } finally {
    await session.close();
  }
}

export async function getStats(): Promise<Stats> {
  const session = getSession();
  try {
    const result = await session.executeRead(async (tx) => {
      return tx.run(`
        MATCH (p:Rewind_Project)
        WITH count(p) as projectCount
        MATCH (c:Rewind_Conversation)
        WITH projectCount, count(c) as convCount
        MATCH (m:Rewind_Message)
        WITH projectCount, convCount,
             count(m) as msgCount,
             sum(CASE WHEN m.type = 'user' THEN 1 ELSE 0 END) as userMsgs,
             sum(CASE WHEN m.type = 'assistant' THEN 1 ELSE 0 END) as assistantMsgs,
             sum(COALESCE(m.inputTokens, 0)) as inputTokens,
             sum(COALESCE(m.outputTokens, 0)) as outputTokens,
             collect(m.model) as models
        RETURN projectCount, convCount, msgCount, userMsgs, assistantMsgs,
               inputTokens, outputTokens, models
      `);
    });

    if (result.records.length === 0) {
      return {
        totalConversations: 0,
        totalProjects: 0,
        totalMessages: 0,
        userMessageCount: 0,
        assistantMessageCount: 0,
        totalTokens: 0,
        inputTokens: 0,
        outputTokens: 0,
        mostUsedModel: '',
        modelUsageCount: 0,
        modelDistribution: {},
        timelineData: [],
      };
    }

    const record = result.records[0];
    const models: string[] = record.get('models').filter(Boolean);

    // Calculate model distribution
    const modelDistribution: Record<string, number> = {};
    for (const model of models) {
      modelDistribution[model] = (modelDistribution[model] || 0) + 1;
    }

    const mostUsedModel =
      Object.entries(modelDistribution).sort(([, a], [, b]) => b - a)[0]?.[0] || '';
    const modelUsageCount = modelDistribution[mostUsedModel] || 0;

    const inputTokens = toNumber(record.get('inputTokens'));
    const outputTokens = toNumber(record.get('outputTokens'));

    return {
      totalProjects: toNumber(record.get('projectCount')),
      totalConversations: toNumber(record.get('convCount')),
      totalMessages: toNumber(record.get('msgCount')),
      userMessageCount: toNumber(record.get('userMsgs')),
      assistantMessageCount: toNumber(record.get('assistantMsgs')),
      inputTokens,
      outputTokens,
      totalTokens: inputTokens + outputTokens,
      mostUsedModel,
      modelUsageCount,
      modelDistribution,
      timelineData: [], // TODO: Add timeline query
    };
  } finally {
    await session.close();
  }
}
