import { useEffect, useState } from "react";
import { resolveTopicSlug } from "../lib/legacy-topic-route";

function resolveSlug(): string | null {
  return resolveTopicSlug(window.location.search, window.location.hash);
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
