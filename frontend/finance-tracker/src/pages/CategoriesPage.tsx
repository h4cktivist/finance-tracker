import { useMemo, useState } from 'react'
import { ChevronDown, ChevronRight, Folder, Pencil, Plus, Trash2 } from 'lucide-react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import {
  useCategoriesTree,
  useCategories,
  useCreateCategory,
  useDeleteCategory,
  useUpdateCategory,
} from '@/hooks/useQueries'
import type { Category, CategoryTreeNode, CategoryType } from '@/lib/types'
import { Modal } from '@/components/Modal'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { EmptyState } from '@/components/EmptyState'
import { ColorPicker } from '@/components/ColorPicker'
import { IconPicker } from '@/components/IconPicker'
import { getIcon } from '@/lib/icons'
import { handleApiError } from '@/lib/errors'

const schema = z.object({
  name: z.string().min(1, 'Введите название').max(255),
  type: z.enum(['expense', 'income']),
  parent_category_id: z.string().nullable().optional(),
  color: z.string().max(20).nullable().optional(),
  icon: z.string().max(50).nullable().optional(),
  is_essential: z.boolean().optional(),
})

type FormValues = z.infer<typeof schema>

export function CategoriesPage() {
  const [tab, setTab] = useState<CategoryType>('expense')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Category | null>(null)
  const [deleting, setDeleting] = useState<Category | null>(null)
  const [parentForCreate, setParentForCreate] = useState<Category | null>(null)
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  const tree = useCategoriesTree()
  const flat = useCategories()

  const create = useCreateCategory()
  const update = useUpdateCategory()
  const remove = useDeleteCategory()

  const filteredTree = useMemo(
    () => (tree.data ?? []).filter((n) => n.type === tab),
    [tree.data, tab],
  )

  const parentOptions = useMemo(
    () => (flat.data ?? []).filter((c) => c.type === tab && c.parent_category_id === null),
    [flat.data, tab],
  )

  function toggle(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function openCreate(parent?: Category) {
    setEditing(null)
    setParentForCreate(parent ?? null)
    setOpen(true)
  }
  function openEdit(c: Category) {
    setEditing(c)
    setParentForCreate(null)
    setOpen(true)
  }

  async function handleDelete() {
    if (!deleting) return
    try {
      await remove.mutateAsync(deleting.id)
      toast.success('Категория удалена')
      setDeleting(null)
    } catch (e) {
      handleApiError(e)
    }
  }

  return (
    <>
      <div className="row-between">
        <div className="row" style={{ background: 'var(--panel)', border: '1px solid var(--border)', borderRadius: 12, padding: 4 }}>
          <button
            className={`btn btn-sm ${tab === 'expense' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setTab('expense')}
          >
            Расходы
          </button>
          <button
            className={`btn btn-sm ${tab === 'income' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setTab('income')}
          >
            Доходы
          </button>
        </div>
        <button className="btn btn-primary" onClick={() => openCreate()}>
          <Plus size={16} /> Новая категория
        </button>
      </div>

      <div className="card">
        {tree.isLoading ? (
          <div className="muted">Загрузка…</div>
        ) : filteredTree.length === 0 ? (
          <EmptyState
            title="Нет категорий"
            description={`Создайте свою первую ${tab === 'expense' ? 'расходную' : 'доходную'} категорию`}
            action={<button className="btn btn-primary" onClick={() => openCreate()}><Plus size={16} /> Создать</button>}
            icon={<Folder size={36} />}
          />
        ) : (
          <div className="col" style={{ gap: 4 }}>
            {filteredTree.map((node) => (
              <TreeRow
                key={node.id}
                node={node}
                depth={0}
                expanded={expanded}
                onToggle={toggle}
                onEdit={openEdit}
                onDelete={setDeleting}
                onAddChild={openCreate}
              />
            ))}
          </div>
        )}
      </div>

      <CategoryFormModal
        open={open}
        onClose={() => setOpen(false)}
        editing={editing}
        parent={parentForCreate}
        defaultType={tab}
        rootOptions={parentOptions}
        onSubmit={async (values) => {
          try {
            if (editing) {
              await update.mutateAsync({
                id: editing.id,
                data: {
                  name: values.name,
                  color: values.color || null,
                  icon: values.icon || null,
                  is_essential: values.is_essential,
                  parent_category_id: values.parent_category_id || null,
                },
              })
              toast.success('Категория обновлена')
            } else {
              await create.mutateAsync({
                name: values.name,
                type: values.type,
                parent_category_id: values.parent_category_id || null,
                color: values.color || null,
                icon: values.icon || null,
                is_essential: values.is_essential ?? true,
              })
              toast.success('Категория создана')
            }
            setOpen(false)
          } catch (e) {
            handleApiError(e)
          }
        }}
        submitting={create.isPending || update.isPending}
      />

      <ConfirmDialog
        open={!!deleting}
        title="Удалить категорию?"
        description={`«${deleting?.name}» будет удалена.`}
        confirmText="Удалить"
        danger
        onConfirm={handleDelete}
        onCancel={() => setDeleting(null)}
        loading={remove.isPending}
      />
    </>
  )
}

function TreeRow({
  node, depth, expanded, onToggle, onEdit, onDelete, onAddChild,
}: {
  node: CategoryTreeNode
  depth: number
  expanded: Set<string>
  onToggle: (id: string) => void
  onEdit: (c: Category) => void
  onDelete: (c: Category) => void
  onAddChild: (parent: Category) => void
}) {
  const hasChildren = node.children.length > 0
  const isOpen = expanded.has(node.id)
  const Icon = getIcon(node.icon)
  return (
    <>
      <div
        className="row-between"
        style={{
          padding: '10px 12px',
          paddingLeft: 12 + depth * 22,
          borderRadius: 10,
          background: depth === 0 ? 'rgba(11,16,32,0.4)' : 'transparent',
          border: depth === 0 ? '1px solid var(--border)' : 'none',
        }}
      >
        <div className="row" style={{ gap: 8 }}>
          {hasChildren ? (
            <button
              type="button"
              className="btn btn-ghost btn-icon btn-sm"
              onClick={() => onToggle(node.id)}
              aria-label="Раскрыть"
            >
              {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </button>
          ) : (
            <span style={{ width: 26 }} />
          )}
          {Icon ? (
            <span
              style={{
                width: 26, height: 26, borderRadius: 7,
                background: node.color ? node.color + '22' : 'rgba(120,134,200,0.1)',
                color: node.color ?? 'var(--text-muted)',
                display: 'grid', placeItems: 'center',
              }}
            >
              <Icon size={14} />
            </span>
          ) : (
            node.color && <span className="color-swatch" style={{ background: node.color }} />
          )}
          <span style={{ fontWeight: depth === 0 ? 500 : 400 }}>{node.name}</span>
          {!node.is_essential && (
            <span className="badge badge-muted category-nonessential-badge">не обязат.</span>
          )}
        </div>
        <div className="row" style={{ gap: 4 }}>
          {depth === 0 && (
            <button
              className="btn btn-ghost btn-icon btn-sm"
              onClick={() => onAddChild(node)}
              title="Добавить подкатегорию"
            >
              <Plus size={14} />
            </button>
          )}
          <button className="btn btn-ghost btn-icon btn-sm" onClick={() => onEdit(node)}>
            <Pencil size={14} />
          </button>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={() => onDelete(node)}>
            <Trash2 size={14} />
          </button>
        </div>
      </div>
      {hasChildren && isOpen && node.children.map((c) => (
        <TreeRow
          key={c.id}
          node={c}
          depth={depth + 1}
          expanded={expanded}
          onToggle={onToggle}
          onEdit={onEdit}
          onDelete={onDelete}
          onAddChild={onAddChild}
        />
      ))}
    </>
  )
}

function CategoryFormModal({
  open, onClose, editing, parent, defaultType, rootOptions, onSubmit, submitting,
}: {
  open: boolean
  onClose: () => void
  editing: Category | null
  parent: Category | null
  defaultType: CategoryType
  rootOptions: Category[]
  onSubmit: (values: FormValues) => void
  submitting: boolean
}) {
  const {
    register, handleSubmit, formState: { errors }, control,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    values: editing
      ? {
          name: editing.name,
          type: editing.type,
          parent_category_id: editing.parent_category_id ?? '',
          color: editing.color ?? '',
          icon: editing.icon ?? '',
          is_essential: editing.is_essential,
        }
      : {
          name: '',
          type: parent?.type ?? defaultType,
          parent_category_id: parent?.id ?? '',
          color: '',
          icon: '',
          is_essential: true,
        },
  })

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={editing ? 'Редактировать категорию' : 'Новая категория'}
      size="lg"
    >
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="field">
          <label>Название</label>
          <input className="input" {...register('name')} />
          {errors.name && <span className="field-error">{errors.name.message}</span>}
        </div>

        {!editing && (
          <div className="form-row form-row-2" style={{ marginTop: 12 }}>
            <div className="field">
              <label>Тип</label>
              <select className="select" {...register('type')} disabled={!!parent}>
                <option value="expense">Расход</option>
                <option value="income">Доход</option>
              </select>
            </div>
            <div className="field">
              <label>Родительская категория</label>
              <select className="select" {...register('parent_category_id')}>
                <option value="">Без родителя (корневая)</option>
                {rootOptions.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>
        )}

        <div className="form-row form-row-2" style={{ marginTop: 12 }}>
          <Controller
            control={control}
            name="color"
            render={({ field }) => (
              <ColorPicker
                label="Цвет"
                value={field.value}
                onChange={(c) => field.onChange(c ?? '')}
              />
            )}
          />
          <Controller
            control={control}
            name="icon"
            render={({ field }) => (
              <IconPicker
                label="Иконка"
                value={field.value}
                onChange={(i) => field.onChange(i ?? '')}
              />
            )}
          />
        </div>

        <label className="row" style={{ marginTop: 14, gap: 8, cursor: 'pointer' }}>
          <input type="checkbox" {...register('is_essential')} />
          <span>Обязательный расход / доход</span>
        </label>

        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Отмена</button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? '…' : editing ? 'Сохранить' : 'Создать'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
