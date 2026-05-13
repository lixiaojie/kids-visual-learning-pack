import { useEffect, useState } from "react";

function resolveSlug(): string | null {
  const params = new URLSearchParams(window.location.search);
  const queryTopic = params.get("topic");
  if (queryTopic) return decodeURIComponent(queryTopic);

  const match = window.location.hash.match(/^#topic\/(.+)$/);
  return match?.[1] ? decodeURIComponent(match[1]) : null;
}

export function useHashRoute() {
  const [slug, setSlug] = useState(resolveSlug);

  useEffect(() => {
    const handler = () => {
      setSlug(resolveSlug());
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", handler);
    window.addEventListener("popstate", handler);
    return () => {
      window.removeEventListener("hashchange", handler);
      window.removeEventListener("popstate", handler);
    };
  }, []);

  return slug;
}
