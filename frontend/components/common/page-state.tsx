import { Card } from "@/components/ui/card";

export function PageState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <Card className="flex min-h-56 items-center justify-center text-center">
      <div>
        <h2 className="font-display text-2xl font-semibold">{title}</h2>
        <p className="mt-2 max-w-xl text-sm text-[var(--muted-foreground)]">{description}</p>
      </div>
    </Card>
  );
}
