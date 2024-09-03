import io

class DataExporter:
    @staticmethod
    def export_to_csv(df, filename):
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return buffer.getvalue()
