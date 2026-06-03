import { useState } from 'react'
import { Pencil, Plus, Tag as TagIcon, Trash2 } from 'lucide-react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { useCreateTag, useDeleteTag, useTags, useUpdateTag } from '@/hooks/useQueries'
import type { Tag } from '@/lib/types'
import { Modal } from '@/components/Modal'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { EmptyState } from '@/components/EmptyState'
import { ColorPicker } from '@/components/ColorPicker'
import { handleApiError } from '@/lib/errors'

const schema = z.object({
  name: z.string().min(1, 'Введите название').max(100),
  color: z.string().max(20).nullable().optional(),
})

type FormValues = z.infer<typeof schema>

export function TagsPage() {
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Tag | null>(null)
  const [deleting, setDeleting] = useState<Tag | null>(null)

  const { data, isLoading } = useTags()
  const create = useCreateTag()
  const update = useUpdateTag()
  const remove = useDeleteTag()

  function openCreate() {
    setEditing(null)
    setOpen(true)
  }
  function openEdit(t: Tag) {
    setEditing(t)
    setOpen(true)
  }

  async function handleDelete() {
    if (!deleting) return
    try {
      await remove.mutateAsync(deleting.id)
      toast.success('Тег удалён')
      setDeleting(null)
    } catch (e) {
      handleApiError(e)
    }
  }

  return (
    <>
      <div className="row-between page-toolbar">
        <div className="muted">Используйте теги для гибкой категоризации операций</div>
        <button className="btn btn-primary" onClick={openCreate}>
          <Plus size={16} /> Новый тег
        </button>
      </div>

      <div className="card">
        {isLoading ? (
          <div className="muted">Загрузка…</div>
        ) : !data || data.length === 0 ? (
          <EmptyState
            title="Пока нет тегов"
            description="Создайте теги для удобной фильтрации транзакций"
            icon={<TagIcon size={36} />}
            action={<button className="btn btn-primary" onClick={openCreate}><Plus size={16} /> Создать</button>}
          />
        ) : (
          <div className="row" style={{ gap: 10, flexWrap: 'wrap' }}>
            {data.map((t) => (
              <div
                key={t.id}
                className="pill"
                style={{
                  padding: '6px 10px 6px 12px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span
                  className="color-swatch"
                  style={{ background: t.color || '#7c5cff', margin: 0 }}
                />
                <span>{t.name}</span>
                <button
                  className="btn btn-ghost btn-icon"
                  style={{ padding: 2 }}
                  onClick={() => openEdit(t)}
                  aria-label="Редактировать"
                >
                  <Pencil size={12} />
                </button>
                <button
                  className="btn btn-ghost btn-icon"
                  style={{ padding: 2 }}
                  onClick={() => setDeleting(t)}
                  aria-label="Удалить"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <TagFormModal
        open={open}
        onClose={() => setOpen(false)}
        editing={editing}
        onSubmit={async (values) => {
          try {
            if (editing) {
              await update.mutateAsync({ id: editing.id, data: values })
              toast.success('Тег обновлён')
            } else {
              await create.mutateAsync(values)
              toast.success('Тег создан')
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
        title="Удалить тег?"
        description={`Тег «${deleting?.name}» больше не будет применяться к новым операциям.`}
        confirmText="Удалить"
        danger
        onConfirm={handleDelete}
        onCancel={() => setDeleting(null)}
        loading={remove.isPending}
      />
    </>
  )
}

function TagFormModal({
  open, onClose, editing, onSubmit, submitting,
}: {
  open: boolean
  onClose: () => void
  editing: Tag | null
  onSubmit: (values: FormValues) => void
  submitting: boolean
}) {
  const {
    register, handleSubmit, formState: { errors }, control,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    values: editing
      ? { name: editing.name, color: editing.color ?? '' }
      : { name: '', color: '' },
  })

  return (
    <Modal open={open} onClose={onClose} title={editing ? 'Редактировать тег' : 'Новый тег'}>
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="field">
          <label>Название</label>
          <input className="input" {...register('name')} />
          {errors.name && <span className="field-error">{errors.name.message}</span>}
        </div>
        <div style={{ marginTop: 12 }}>
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
        </div>
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
