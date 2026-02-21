import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { apiFetch } from '../api'

// Tool component registry - add new tools here as they're migrated
import HtmlToMarkdown from '../tools/HtmlToMarkdown'
import MarkdownStripper from '../tools/MarkdownStripper'
import ColorSwatchInjector from '../tools/ColorSwatchInjector'
import TableCreator from '../tools/TableCreator'
import MarkdownTableConverter from '../tools/MarkdownTableConverter'
import ItemsToLinks from '../tools/ItemsToLinks'
import HomeAutomationCategorizer from '../tools/HomeAutomationCategorizer'

interface ToolMeta {
    id: string
    long_title: string
    description: string
    category: string
}

// Map tool IDs to their React components
const TOOL_COMPONENTS: Record<string, React.ComponentType> = {
    HtmlToMarkdown,
    MarkdownStripper,
    ColorSwatchInjector,
    TableCreator,
    MarkdownTableConverter,
    ItemsToLinks,
    HomeAutomationCategorizer,
}

export default function ToolPage() {
    const { toolId } = useParams<{ toolId: string }>()

    const { data: tools = [] } = useQuery<ToolMeta[]>({
        queryKey: ['tools'],
        queryFn: () => apiFetch('/tools'),
    })

    const tool = tools.find(t => t.id === toolId)
    const ToolComponent = toolId ? TOOL_COMPONENTS[toolId] : undefined

    if (!tool && tools.length > 0) {
        return <div className="error-box">Tool "{toolId}" not found.</div>
    }

    return (
        <div className="tool-page">
            <div className="tool-page-header">
                {tool && (
                    <>
                        <div className="category-badge">{tool.category}</div>
                        <h1 className="tool-page-title" style={{ marginTop: 8 }}>{tool.long_title}</h1>
                        <p className="tool-page-desc">{tool.description}</p>
                    </>
                )}
            </div>

            {ToolComponent ? (
                <ToolComponent />
            ) : (
                <div className="info-box" style={{ textAlign: 'center', padding: '40px 20px' }}>
                    <div style={{ fontSize: 32, marginBottom: 12 }}>🚧</div>
                    <div style={{ fontWeight: 600, marginBottom: 6, color: 'var(--text-primary)' }}>
                        React version coming soon
                    </div>
                    <div>
                        This tool is available in the{' '}
                        <a
                            href="http://localhost:8501"
                            target="_blank"
                            rel="noreferrer"
                            style={{ color: 'var(--accent)' }}
                        >
                            Streamlit version
                        </a>
                        {' '}while the migration is in progress.
                    </div>
                </div>
            )}
        </div>
    )
}
