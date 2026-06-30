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
import ObsidianNotePlacement from '../tools/ObsidianNotePlacement'
import BmadProjectStatus from '../tools/BmadProjectStatus'
import DragonKeeper from '../tools/DragonKeeper'
import WireframeVisualizer from '../tools/WireframeVisualizer'
import HomeAssistantSensors from '../tools/HomeAssistantSensors'
import HomeAssistantDashboard from '../tools/HomeAssistantDashboard'

interface ToolMeta {
    id: string
    long_title: string
    description: string
    category: string
}

type ToolComponent = React.ComponentType & { HeaderExtra?: React.ComponentType; fullBleed?: boolean }

// Map tool IDs to their React components
const TOOL_COMPONENTS: Record<string, ToolComponent> = {
    HtmlToMarkdown,
    MarkdownStripper,
    ColorSwatchInjector,
    TableCreator,
    MarkdownTableConverter,
    ItemsToLinks,
    HomeAutomationCategorizer,
    ObsidianNotePlacement,
    BmadProjectStatus,
    DragonKeeper,
    WireframeVisualizer,
    HomeAssistantSensors,
    HomeAssistantDashboard,
}

export default function ToolPage() {
    const { toolId } = useParams<{ toolId: string }>()

    const { data: tools = [] } = useQuery<ToolMeta[]>({
        queryKey: ['tools'],
        queryFn: () => apiFetch('/tools'),
    })

    const tool = tools.find(t => t.id === toolId)
    const ToolComponent: ToolComponent | undefined = toolId ? TOOL_COMPONENTS[toolId] : undefined
    const HeaderExtra = ToolComponent?.HeaderExtra
    const fullBleed = ToolComponent?.fullBleed

    if (!tool && tools.length > 0) {
        return <div className="error-box">Tool "{toolId}" not found.</div>
    }

    return (
        <div className={fullBleed ? 'tool-page tool-page-full-bleed' : 'tool-page'}>
            <div className="tool-page-header">
                {tool && (
                    <>
                        <div className="category-badge">{tool.category}</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: 8 }}>
                            <h1 className="tool-page-title">{tool.long_title}</h1>
                            {HeaderExtra && <HeaderExtra />}
                        </div>
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
