import React, { useEffect, useState } from "react";
import { AXIOS_INSTANCE } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useWorkspaces } from "@/features/workspaces/WorkspaceContext";
import { Download, File, FileText, HardDrive, Image as ImageIcon, Trash2, Upload } from "lucide-react";

interface StoredFile {
  id: string;
  filename: string;
  content_type: string;
  file_size_bytes: number;
  storage_backend: string;
  is_public: boolean;
  created_at: string;
  download_url: string;
}

export const StorageView: React.FC = () => {
  const { activeWorkspace } = useWorkspaces();
  const [files, setFiles] = useState<StoredFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<globalThis.File | null>(null);
  const [isPublic, setIsPublic] = useState(false);

  const fetchFiles = async () => {
    if (!activeWorkspace) return;
    setLoading(true);
    try {
      const res = await AXIOS_INSTANCE.get<StoredFile[]>(
        `/api/v1/workspaces/${activeWorkspace.id}/storage/files`
      );
      setFiles(res.data);
    } catch (err) {
      console.error("Erro ao carregar arquivos:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, [activeWorkspace?.id]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspace || !selectedFile) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("is_public", String(isPublic));

    try {
      await AXIOS_INSTANCE.post(
        `/api/v1/workspaces/${activeWorkspace.id}/storage/upload`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      setSelectedFile(null);
      fetchFiles();
    } catch (err) {
      console.error("Erro ao fazer upload do arquivo:", err);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (fileId: string) => {
    if (!activeWorkspace) return;
    if (!confirm("Tem certeza que deseja excluir permanentemente este arquivo?")) return;

    try {
      await AXIOS_INSTANCE.delete(`/api/v1/workspaces/${activeWorkspace.id}/storage/files/${fileId}`);
      fetchFiles();
    } catch (err) {
      console.error(err);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (contentType: string) => {
    if (contentType.startsWith("image/")) {
      return <ImageIcon className="h-4 w-4 text-blue-500" />;
    }
    if (contentType.includes("pdf") || contentType.includes("text")) {
      return <FileText className="h-4 w-4 text-orange-500" />;
    }
    return <File className="h-4 w-4 text-muted-foreground" />;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <HardDrive className="h-6 w-6 text-primary" />
            Storage & Arquivos
          </h2>
          <p className="text-sm text-muted-foreground">
            Armazenamento desacoplado compatível com sistema de arquivos local e AWS S3 / MinIO.
          </p>
        </div>
      </div>

      {/* Card de Upload */}
      <Card className="border-primary/30 bg-card/60 backdrop-blur">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Upload className="h-4 w-4 text-primary" />
            Enviar Novo Arquivo
          </CardTitle>
          <CardDescription className="text-xs">
            Tamanho máximo de 25 MB. Sanitização automática de nomes e validação MIME no servidor.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleUpload} className="flex flex-col sm:flex-row items-center gap-4">
            <input
              type="file"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="text-xs file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90 cursor-pointer"
            />

            <label className="flex items-center gap-2 text-xs cursor-pointer">
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                className="rounded border-gray-300 text-primary focus:ring-primary"
              />
              <span>Arquivo Público</span>
            </label>

            <Button
              type="submit"
              disabled={!selectedFile || uploading}
              className="sm:ml-auto gap-2"
              size="sm"
            >
              {uploading ? (
                <>
                  <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                  Enviando...
                </>
              ) : (
                <>
                  <Upload className="h-3.5 w-3.5" />
                  Fazer Upload
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Lista de Arquivos */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-muted/50 border-b text-muted-foreground uppercase font-semibold text-[11px]">
                <tr>
                  <th className="py-3 px-4">Nome do Arquivo</th>
                  <th className="py-3 px-4">Tipo</th>
                  <th className="py-3 px-4">Tamanho</th>
                  <th className="py-3 px-4">Backend</th>
                  <th className="py-3 px-4">Data</th>
                  <th className="py-3 px-4 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12">
                      <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent mx-auto" />
                    </td>
                  </tr>
                ) : files.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12 text-muted-foreground">
                      Nenhum arquivo armazenado neste workspace.
                    </td>
                  </tr>
                ) : (
                  files.map((file) => (
                    <tr key={file.id} className="hover:bg-muted/20 transition-colors">
                      <td className="py-3 px-4 font-semibold text-foreground flex items-center gap-2">
                        {getFileIcon(file.content_type)}
                        <span className="truncate max-w-xs">{file.filename}</span>
                      </td>
                      <td className="py-3 px-4 text-muted-foreground">{file.content_type}</td>
                      <td className="py-3 px-4 font-mono text-muted-foreground">
                        {formatFileSize(file.file_size_bytes)}
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="outline" className="text-[10px] uppercase font-mono">
                          {file.storage_backend}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-muted-foreground">
                        {new Date(file.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <a
                            href={file.download_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1 text-primary hover:bg-primary/10 rounded"
                            title="Baixar Arquivo"
                          >
                            <Download className="h-4 w-4" />
                          </a>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(file.id)}
                            className="h-7 w-7 p-0 text-destructive hover:bg-destructive/10"
                            title="Excluir"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
