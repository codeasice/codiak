import CategoryDetail from './category-detail'

interface CategoryDetailWrapperProps {
  categoryId: string
  onBack: () => void
}

export default function CategoryDetailWrapper({ categoryId, onBack }: CategoryDetailWrapperProps) {
  return <CategoryDetail categoryId={categoryId} onBack={onBack} />
}
