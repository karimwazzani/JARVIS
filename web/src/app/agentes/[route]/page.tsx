import { AgentWorkspacePage } from "../../dashboard-ui";

export default async function AgentPage({
  params,
}: {
  params: Promise<{ route: string }>;
}) {
  const { route } = await params;
  return <AgentWorkspacePage route={route} />;
}
