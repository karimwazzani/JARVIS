import { NextRequest, NextResponse } from "next/server";

function unauthorized() {
  return new NextResponse("Authentication required", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="JARVIS Dashboard"',
    },
  });
}

export function proxy(request: NextRequest) {
  const username = process.env.DASHBOARD_USER;
  const password = process.env.DASHBOARD_PASSWORD;

  if (!username || !password) {
    return NextResponse.next();
  }

  const authHeader = request.headers.get("authorization");
  if (!authHeader?.startsWith("Basic ")) {
    return unauthorized();
  }

  try {
    const encoded = authHeader.slice("Basic ".length);
    const [providedUser, providedPassword] = atob(encoded).split(":");
    if (providedUser === username && providedPassword === password) {
      return NextResponse.next();
    }
  } catch {
    return unauthorized();
  }

  return unauthorized();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
