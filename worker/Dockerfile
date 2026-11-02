FROM mcr.microsoft.com/dotnet/sdk:10.0.403-noble AS build
WORKDIR /source
COPY *.csproj packages.lock.json ./
RUN dotnet restore --locked-mode
COPY . .
RUN dotnet publish -c Release -o /app --self-contained false --no-restore

FROM mcr.microsoft.com/dotnet/runtime:10.0.14-noble
WORKDIR /app
COPY --from=build /app .
USER app
ENTRYPOINT ["dotnet", "Worker.dll"]
