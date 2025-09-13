export interface Message {
  sender: "user" | "bot";
  text?: string;
  words?: string[];
  loading?: boolean;
  trace?: Record<string, unknown>;
  sources?: Source[];
}

export interface Source {
  file: string;
  page?: number | null;
  text: string;
}
