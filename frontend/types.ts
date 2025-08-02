export interface Message {
  sender: "user" | "bot";
  text?: string;
  words?: string[];
  loading?: boolean;
  trace?: Record<string, unknown>;
}
