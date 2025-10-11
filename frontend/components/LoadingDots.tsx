const LoadingDots = () => (
  <div className="flex items-center gap-1">
    <span
      className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
      style={{ animationDelay: "0ms" }}
    ></span>
    <span
      className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
      style={{ animationDelay: "150ms" }}
    ></span>
    <span
      className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
      style={{ animationDelay: "300ms" }}
    ></span>
  </div>
);

export default LoadingDots;
